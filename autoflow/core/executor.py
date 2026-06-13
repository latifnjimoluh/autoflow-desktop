"""Moteur d'exécution séquentiel des workflows.

Le moteur est volontairement **indépendant de Qt** : il communique via de
simples fonctions de rappel (``log``, ``on_status``, ``on_iteration``,
``on_action``), ce qui le rend entièrement testable. L'interface graphique
l'enveloppe dans un thread et relaie ces rappels en signaux Qt.

Pause et arrêt sont gérés par des :class:`threading.Event`, et toutes les
attentes sont **interruptibles** (l'arrêt prend effet immédiatement).
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from ..models.workflow import Workflow
from .scheduler import Scheduler

# Types de rappels.
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
        sleep_func: Callable[[float], None] | None = None,
        continue_on_error: bool = True,
    ) -> None:
        self.workflow = workflow
        self.inputs = inputs
        self.windows = windows
        self._log_cb: LogFunc = log or _noop
        self._status_cb: StatusFunc = on_status or _noop
        self._iter_cb: IntFunc = on_iteration or _noop
        self._action_cb: ActionFunc = on_action or _noop
        self.continue_on_error = continue_on_error

        self._stop = threading.Event()
        self._pause = threading.Event()  # positionné => en pause
        self._sleeper = sleep_func or self._interruptible_sleep
        self.iterations_done = 0

    # -- Commandes ---------------------------------------------------------
    def request_stop(self) -> None:
        """Demande l'arrêt du workflow (prend effet à la prochaine vérification)."""
        self._stop.set()
        self._pause.clear()  # ne pas rester bloqué en pause

    def pause(self) -> None:
        """Met l'exécution en pause."""
        self._pause.set()
        self._status_cb("paused")

    def resume(self) -> None:
        """Reprend l'exécution après une pause."""
        self._pause.clear()
        self._status_cb("running")

    def is_stopped(self) -> bool:
        """Indique si un arrêt a été demandé."""
        return self._stop.is_set()

    def is_paused(self) -> bool:
        """Indique si l'exécution est en pause."""
        return self._pause.is_set()

    # -- Attentes ----------------------------------------------------------
    def _interruptible_sleep(self, seconds: float) -> None:
        """Attente par défaut, interrompue immédiatement par une demande d'arrêt."""
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
        """Bloque tant que l'exécution est en pause (sans bloquer l'arrêt)."""
        while self._pause.is_set() and not self._stop.is_set():
            self._stop.wait(timeout=0.05)

    # -- Journalisation ----------------------------------------------------
    def _log(self, message: str, level: str = "info") -> None:
        """Relaie un message vers la fonction de log fournie."""
        self._log_cb(message, level)

    # -- Boucle principale -------------------------------------------------
    def run(self) -> int:
        """Exécute le workflow jusqu'au bout (ou jusqu'à l'arrêt). Renvoie le
        nombre d'itérations réalisées."""
        scheduler = Scheduler(self.workflow.schedule)
        self._stop.clear()
        self._pause.clear()
        self.iterations_done = 0
        self._status_cb("running")
        self._log(f"Démarrage du workflow « {self.workflow.name} ».", "info")

        try:
            initial = scheduler.initial_delay()
            if initial > 0:
                self._log(f"Attente initiale de {initial:.0f} s avant exécution.", "info")
                self._sleep(initial)

            while scheduler.should_run(self.iterations_done):
                if self.is_stopped():
                    raise StopRequested
                self._run_iteration(self.iterations_done + 1)
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

    def _run_iteration(self, index: int) -> None:
        """Exécute une fois la séquence d'actions activées."""
        context: dict[str, Any] = {
            "sleep": self._sleep,
            "log": self._log,
            "iteration": index,
        }
        for action in self.workflow.actions:
            if self.is_stopped():
                raise StopRequested
            self._wait_while_paused()
            if self.is_stopped():
                raise StopRequested
            if not getattr(action, "enabled", True):
                continue

            self._action_cb(action, index)
            self._log(f"→ {_summary(action)}", "action")
            try:
                action.execute(self.inputs, self.windows, context)
            except StopRequested:
                raise
            except Exception as exc:  # noqa: BLE001 - politique d'erreur explicite
                if type(exc).__name__ == "FailSafeException":
                    self._log("Failsafe déclenché : arrêt d'urgence.", "error")
                    raise StopRequested from exc
                self._log(f"Erreur sur « {_summary(action)} » : {exc}", "error")
                if not self.continue_on_error:
                    raise StopRequested from exc

            delay = float(getattr(action, "delay_after", 0.0) or 0.0)
            if delay > 0:
                self._sleep(delay)


def _summary(action: Any) -> str:
    """Renvoie le résumé d'une action, avec repli robuste."""
    summary = getattr(action, "summary", None)
    if callable(summary):
        try:
            return summary()
        except Exception:  # noqa: BLE001 - le résumé ne doit jamais casser le moteur
            pass
    return getattr(action, "type_name", "action")
