"""Moteur d'exécution séquentiel des workflows (avec contrôle de flux).

Le moteur reste **indépendant de Qt** (rappels simples) et entièrement testable.
Il gère :

- l'exécution de séquences **imbriquées** (conditions, boucles) via
  ``context["run_actions"]`` ;
- un **magasin de variables** partagé (``context["variables"]``) ;
- la **pause/arrêt** interruptibles et le **mode pas-à-pas** ;
- une **politique par action** : ré-essais (retries), délai entre tentatives et
  comportement en cas d'échec.

La compatibilité ascendante est préservée : un workflow « plat » (liste d'actions
sans imbrication) s'exécute exactement comme avant.
"""

from __future__ import annotations

import random
import threading
from collections.abc import Callable
from typing import Any

from ..models.workflow import Workflow
from .clipboard import ClipboardBackend
from .ocr import OcrBackend
from .scheduler import Scheduler
from .variables import VariableStore
from .vision import VisionBackend

LogFunc = Callable[[str, str], None]
StatusFunc = Callable[[str], None]
IntFunc = Callable[[int], None]
ActionFunc = Callable[[Any, int], None]


class StopRequested(Exception):
    """Signal interne : l'arrêt du workflow a été demandé."""


def _noop(*_args: Any, **_kwargs: Any) -> None:
    """Rappel par défaut : ne fait rien."""


class Executor:
    """Exécute un :class:`Workflow` selon son planning."""

    def __init__(
        self,
        workflow: Workflow,
        inputs: Any,
        windows: Any,
        log: LogFunc | None = None,
        on_status: StatusFunc | None = None,
        on_iteration: IntFunc | None = None,
        on_action: ActionFunc | None = None,
        on_step: ActionFunc | None = None,
        sleep_func: Callable[[float], None] | None = None,
        continue_on_error: bool = True,
        settings: Any = None,
        workflow_resolver: Callable[[str], Workflow | None] | None = None,
        step_mode: bool = False,
        rng: random.Random | None = None,
    ) -> None:
        self.workflow = workflow
        self.inputs = inputs
        self.windows = windows
        self._log_cb: LogFunc = log or _noop
        self._status_cb: StatusFunc = on_status or _noop
        self._iter_cb: IntFunc = on_iteration or _noop
        self._action_cb: ActionFunc = on_action or _noop
        self._step_cb: ActionFunc = on_step or _noop
        self.continue_on_error = continue_on_error
        self.settings = settings
        self.workflow_resolver = workflow_resolver
        self.step_mode = step_mode
        self._rng = rng or random.Random()

        self._stop = threading.Event()
        self._pause = threading.Event()
        self._step = threading.Event()
        self._sleeper = sleep_func or self._interruptible_sleep
        self.iterations_done = 0
        self.variables = VariableStore()
        # Pile des workflows en cours d'appel (anti-récursion des sous-workflows).
        self.call_stack: list[str] = [workflow.name]

    # -- Commandes ---------------------------------------------------------
    def request_stop(self) -> None:
        """Demande l'arrêt du workflow."""
        self._stop.set()
        self._pause.clear()
        self._step.set()

    def pause(self) -> None:
        """Met l'exécution en pause."""
        self._pause.set()
        self._status_cb("paused")

    def resume(self) -> None:
        """Reprend l'exécution après une pause."""
        self._pause.clear()
        self._status_cb("running")

    def step(self) -> None:
        """Autorise l'exécution de l'action suivante (mode pas-à-pas)."""
        self._step.set()

    def is_stopped(self) -> bool:
        return self._stop.is_set()

    def is_paused(self) -> bool:
        return self._pause.is_set()

    # -- Attentes ----------------------------------------------------------
    def _interruptible_sleep(self, seconds: float) -> None:
        if seconds and seconds > 0:
            self._stop.wait(timeout=float(seconds))

    def _sleep(self, seconds: float) -> None:
        """Attente du moteur : respecte la pause puis l'arrêt."""
        self._wait_while_paused()
        if self.is_stopped():
            raise StopRequested
        if seconds and seconds > 0:
            self._sleeper(float(seconds))
        if self.is_stopped():
            raise StopRequested

    def _wait_while_paused(self) -> None:
        while self._pause.is_set() and not self._stop.is_set():
            self._stop.wait(timeout=0.05)

    def _wait_step(self, action: Any) -> None:
        """En mode pas-à-pas, attend l'autorisation d'exécuter l'action."""
        if not self.step_mode:
            return
        self._step_cb(action, self.variables.iteration)
        while not self._step.is_set() and not self._stop.is_set():
            self._stop.wait(timeout=0.05)
        self._step.clear()

    # -- Journalisation ----------------------------------------------------
    def _log(self, message: str, level: str = "info") -> None:
        self._log_cb(message, level)

    # -- Boucle principale -------------------------------------------------
    def run(self) -> int:
        """Exécute le workflow jusqu'au bout (ou jusqu'à l'arrêt)."""
        scheduler = Scheduler(self.workflow.schedule)
        self._stop.clear()
        self._pause.clear()
        self._step.clear()
        self.iterations_done = 0
        self.variables = VariableStore()
        self._status_cb("running")
        self._log(f"Démarrage du workflow « {self.workflow.name} ».", "info")

        context = self._make_context()
        try:
            initial = scheduler.initial_delay()
            if initial > 0:
                self._log(f"Attente initiale de {initial:.0f} s avant exécution.", "info")
                self._sleep(initial)

            while scheduler.should_run(self.iterations_done):
                if self.is_stopped():
                    raise StopRequested
                self.variables.iteration = self.iterations_done + 1
                context["iteration"] = self.iterations_done + 1
                self.run_sequence(self.workflow.actions, context)
                self.iterations_done += 1
                self._iter_cb(self.iterations_done)
                if scheduler.should_run(self.iterations_done):
                    delay = scheduler.delay_after_iteration()
                    if delay > 0:
                        self._log(
                            f"Itération {self.iterations_done} terminée ; "
                            f"pause de {delay:.0f} s.", "info")
                        self._sleep(delay)
        except StopRequested:
            self._log("Arrêt du workflow demandé.", "warning")
        finally:
            self._status_cb("stopped")
            self._log(
                f"Workflow terminé ({self.iterations_done} itération(s)).", "info")
        return self.iterations_done

    def _make_context(self) -> dict[str, Any]:
        """Construit le contexte d'exécution partagé entre les actions."""
        context: dict[str, Any] = {
            "sleep": self._sleep,
            "log": self._log,
            "variables": self.variables,
            "inputs": self.inputs,
            "windows": self.windows,
            "settings": self.settings,
            "executor": self,
            "iteration": 0,
            "vision": VisionBackend(self.inputs),
            "ocr": OcrBackend(getattr(self.settings, "tesseract_path", "") or ""),
            "clipboard": ClipboardBackend(),
            "workflow_resolver": self.workflow_resolver,
            "call_stack": self.call_stack,
        }
        context["run_actions"] = lambda actions: self.run_sequence(actions, context)
        return context

    def run_sequence(self, actions: list[Any], context: dict[str, Any]) -> None:
        """Exécute une séquence d'actions (réutilisable pour les enfants)."""
        for action in actions:
            if self.is_stopped():
                raise StopRequested
            self._wait_while_paused()
            if self.is_stopped():
                raise StopRequested
            if not getattr(action, "enabled", True):
                continue
            self._wait_step(action)
            if self.is_stopped():
                raise StopRequested
            self._action_cb(action, context["iteration"])
            self._log(f"→ {_summary(action)}", "action")
            self._execute_with_policy(action, context)
            self._sleep_after(action)

    def _execute_with_policy(self, action: Any, context: dict[str, Any]) -> None:
        """Exécute une action en appliquant ré-essais et politique d'échec."""
        attempts = int(getattr(action, "retries", 0) or 0) + 1
        retry_delay = float(getattr(action, "retry_delay", 0.0) or 0.0)
        for attempt in range(1, attempts + 1):
            try:
                action.execute(self.inputs, self.windows, context)
                return
            except StopRequested:
                raise
            except Exception as exc:  # noqa: BLE001 - politique d'erreur explicite
                if type(exc).__name__ == "FailSafeException":
                    self._log("Failsafe déclenché : arrêt d'urgence.", "error")
                    raise StopRequested from exc
                if attempt < attempts:
                    self._log(
                        f"Échec de « {_summary(action)} » "
                        f"(tentative {attempt}/{attempts}) : {exc}", "warning")
                    if retry_delay > 0:
                        self._sleep(retry_delay)
                    continue
                self._log(f"Erreur sur « {_summary(action)} » : {exc}", "error")
                self._apply_failure_policy(action)
                return

    def _apply_failure_policy(self, action: Any) -> None:
        """Applique le comportement en cas d'échec définitif d'une action."""
        policy = getattr(action, "on_error", "inherit")
        if policy == "inherit":
            policy = "continue" if self.continue_on_error else "stop"
        if policy == "stop":
            raise StopRequested

    def _sleep_after(self, action: Any) -> None:
        """Applique le délai après action, avec éventuel jitter « humain »."""
        delay = float(getattr(action, "delay_after", 0.0) or 0.0)
        jitter = float(getattr(action, "delay_jitter", 0.0) or 0.0)
        if jitter > 0:
            delay += self._rng.uniform(0.0, jitter)
        if delay > 0:
            self._sleep(delay)


def _summary(action: Any) -> str:
    """Renvoie le résumé d'une action, avec repli robuste."""
    summary = getattr(action, "summary", None)
    if callable(summary):
        try:
            return summary()
        except Exception:  # noqa: BLE001
            pass
    return getattr(action, "type_name", "action")
