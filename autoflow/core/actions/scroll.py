"""Action : défilement (molette)."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class ScrollAction(Action):
    """Fait défiler vers le haut (valeur positive) ou le bas (négative)."""

    type_name = "scroll"
    label = "Défilement"
    category = "Souris"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("amount", "Crans", "int", -3,
                      help="Positif = vers le haut, négatif = vers le bas."),
        ]

    def validate(self) -> None:
        self._require_number("amount")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        return inputs.scroll(int(self.params["amount"]))

    def summary(self) -> str:
        amount = int(self.params.get("amount", 0))
        sens = "haut" if amount >= 0 else "bas"
        return f"Défilement vers le {sens} ({abs(amount)} crans)"
