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
            ParamSpec("seconds", "Secondes", "float", 1.0),
        ]

    def validate(self) -> None:
        if self._require_number("seconds") < 0:
            raise ValueError("La durée d'attente ne peut pas être négative.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        seconds = float(self.params.get("seconds", 0.0))
        sleeper = (context or {}).get("sleep")
        if callable(sleeper):
            sleeper(seconds)
        else:  # pragma: no cover - repli hors moteur
            import time

            time.sleep(seconds)
        return seconds

    def summary(self) -> str:
        return f"Attendre {self.params.get('seconds')} s"
