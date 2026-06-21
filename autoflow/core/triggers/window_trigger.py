"""Déclencheur par fenêtre : apparition / fermeture / prise de focus.

La détection compare l'état courant des fenêtres à l'état précédent. Cette
logique (``detect``) est **pure et testable** : on lui passe les titres présents
(et la fenêtre active) à chaque tour, sans dépendre d'un vrai bureau.
"""

from __future__ import annotations

import threading
from typing import Any

from .base import ParamSpec, Trigger, TriggerEvent
from .registry import register_trigger

WINDOW_EVENTS = {
    "appears": "Quand la fenêtre apparaît",
    "closes": "Quand la fenêtre se ferme",
    "focus": "Quand la fenêtre prend le focus",
}


@register_trigger
class WindowTrigger(Trigger):
    """Démarre un workflow selon l'état d'une fenêtre (par titre)."""

    type_name = "window_event"
    label = "Déclencheur : fenêtre"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("title", "Fenêtre (titre)", "window", "",
                      placeholder="Ex : Bloc-notes"),
            ParamSpec("event", "Événement", "choice", "appears",
                      choices=list(WINDOW_EVENTS.keys())),
            ParamSpec("match", "Correspondance", "choice", "contains",
                      choices=["contains", "exact"]),
            ParamSpec("interval", "Intervalle de vérification (s)", "float", 1.0,
                      min_value=0.1),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._present = False
        self._focused = False
        self._timer: threading.Timer | None = None
        self._windows_backend: Any = None

    def _matches(self, title: str) -> bool:
        target = str(self.params.get("title", "")).strip().lower()
        title = str(title).lower()
        if str(self.params.get("match", "contains")) == "exact":
            return title == target
        return bool(target) and target in title

    def detect(self, titles: list[str], active_title: str = "") -> TriggerEvent | None:
        """Compare l'état courant au précédent ; renvoie un événement ou ``None``.

        Appelée à chaque tour de scrutation (et par les tests directement).
        """
        present = any(self._matches(t) for t in titles)
        focused = self._matches(active_title)
        event = str(self.params.get("event", "appears"))
        fired: TriggerEvent | None = None
        if event == "appears" and present and not self._present:
            fired = self._event(active_title or self.params.get("title", ""))
        elif event == "closes" and not present and self._present:
            fired = self._event(str(self.params.get("title", "")))
        elif event == "focus" and focused and not self._focused:
            fired = self._event(active_title)
        self._present = present
        self._focused = focused
        return fired

    def _event(self, title: str) -> TriggerEvent:
        return TriggerEvent(
            trigger_type=self.type_name,
            message=f"Fenêtre « {title} » : {WINDOW_EVENTS.get(self.params.get('event'), '')}",
            variables={"window_title": title})

    # -- Live (scrutation périodique) -------------------------------------
    def bind_backend(self, windows_backend: Any) -> None:
        """Injecte le backend de fenêtres utilisé par la scrutation live."""
        self._windows_backend = windows_backend

    def _poll_once(self) -> None:
        backend = self._windows_backend
        if backend is None:
            return
        titles = list(backend.list_titles()) if hasattr(backend, "list_titles") else []
        active = backend.active_title() if hasattr(backend, "active_title") else ""
        event = self.detect(titles, active)
        if event is not None:
            self.fire(event)

    def _start(self) -> bool:
        if self._windows_backend is None:
            return False
        self._schedule()
        return True

    def _schedule(self) -> None:
        interval = float(self.params.get("interval", 1.0) or 1.0)
        self._timer = threading.Timer(interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:  # pragma: no cover - boucle temporisée
        if not self.is_running():
            return
        try:
            self._poll_once()
        finally:
            if self.is_running():
                self._schedule()

    def _stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def summary(self) -> str:
        return (f"{WINDOW_EVENTS.get(self.params.get('event'), 'Fenêtre')} "
                f"« {self.params.get('title')} »")
