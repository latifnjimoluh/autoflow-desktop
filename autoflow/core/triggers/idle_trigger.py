"""Déclencheur par **inactivité** de l'utilisateur (idle) ou session.

L'inactivité est mesurée via l'API Windows (``GetLastInputInfo`` par ``ctypes``).
La logique de décision (``detect``) est pure/testable : on lui fournit le nombre
de secondes d'inactivité. Dégradation propre hors Windows (idle non mesurable).
"""

from __future__ import annotations

import sys
import threading
from typing import Any

from .base import ParamSpec, Trigger, TriggerEvent
from .registry import register_trigger


def get_idle_seconds() -> float:
    """Renvoie les secondes d'inactivité (0.0 si non mesurable, ex. hors Windows)."""
    if not sys.platform.startswith("win"):
        return 0.0
    try:  # pragma: no cover - dépend de Windows
        import ctypes

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
            return millis / 1000.0
    except Exception:  # noqa: BLE001
        return 0.0
    return 0.0


@register_trigger
class IdleTrigger(Trigger):
    """Démarre un workflow après X minutes d'inactivité (déclenché une fois)."""

    type_name = "idle_event"
    label = "Déclencheur : inactivité"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("minutes", "Inactivité (minutes)", "float", 5.0, min_value=0.1),
            ParamSpec("interval", "Intervalle de vérification (s)", "float", 10.0,
                      min_value=1.0),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._fired = False
        self._timer: threading.Timer | None = None
        self._idle_provider = get_idle_seconds

    def detect(self, idle_seconds: float) -> TriggerEvent | None:
        """Déclenche **une fois** quand le seuil est franchi ; réarme au retour."""
        threshold = float(self.params.get("minutes", 5.0)) * 60.0
        if idle_seconds >= threshold:
            if self._fired:
                return None
            self._fired = True
            return TriggerEvent(
                trigger_type=self.type_name,
                message=f"Inactivité ≥ {self.params.get('minutes')} min",
                variables={"idle_seconds": round(idle_seconds, 1)})
        # Activité revenue : on réarme pour le prochain franchissement.
        self._fired = False
        return None

    # -- Live --------------------------------------------------------------
    def bind_provider(self, provider) -> None:
        """Injecte un fournisseur d'inactivité (test/personnalisation)."""
        self._idle_provider = provider

    def _poll_once(self) -> None:
        event = self.detect(float(self._idle_provider()))
        if event is not None:
            self.fire(event)

    def _start(self) -> bool:
        self._schedule()
        return True

    def _schedule(self) -> None:
        interval = float(self.params.get("interval", 10.0) or 10.0)
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
        return f"Après {self.params.get('minutes')} min d'inactivité"
