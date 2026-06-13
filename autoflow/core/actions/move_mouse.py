"""Action : déplacement du curseur de souris."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class MoveMouseAction(Action):
    """Déplace le curseur vers des coordonnées, éventuellement en douceur."""

    type_name = "move_mouse"
    label = "Déplacer la souris"
    category = "Souris"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("x", "X", "int", 0),
            ParamSpec("y", "Y", "int", 0),
            ParamSpec("duration", "Durée (s)", "float", 0.0,
                      help="Durée du déplacement ; 0 = instantané."),
        ]

    def validate(self) -> None:
        self._require_number("x")
        self._require_number("y")
        if self._require_number("duration") < 0:
            raise ValueError("La durée ne peut pas être négative.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        return inputs.move_to(
            int(self.params["x"]),
            int(self.params["y"]),
            duration=float(self.params.get("duration", 0.0)),
        )

    def summary(self) -> str:
        return f"Déplacer vers ({self.params.get('x')}, {self.params.get('y')})"
