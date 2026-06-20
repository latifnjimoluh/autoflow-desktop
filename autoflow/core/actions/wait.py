"""Action : attente (pause)."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class WaitAction(Action):
    """Met l'exécution en pause pendant un nombre de secondes donné.

    L'attente est déléguée au moteur via le ``context`` afin de rester
    interruptible (arrêt/pause) ; à défaut, repli sur ``time.sleep``.
    """

    type_name = "wait"
    label = "Attente"
    category = "Contrôle"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("seconds", "Secondes", "float", 1.0, min_value=0.0),
        ]

    def validate(self) -> None:
        try:
            val = float(self.params.get("seconds", 0.0))
            if val < 0:
                raise ValueError(f"La durée d'attente ne peut pas être négative ({val}).")
        except (TypeError, ValueError):
            raise ValueError("La durée d'attente doit être un nombre valide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        # On redresse au cas où (sécurité exécution).
        seconds = max(0.0, float(self.params.get("seconds", 0.0)))
        sleeper = (context or {}).get("sleep")
        if callable(sleeper):
            sleeper(seconds)
        else:  # pragma: no cover - repli hors moteur
            import time

            time.sleep(seconds)
        return seconds

    def summary(self) -> str:
        return f"Attendre {self.params.get('seconds')} s"
