"""Action : glisser-déposer."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class DragAction(Action):
    """Glisse le curseur d'un point de départ vers un point d'arrivée."""

    type_name = "drag"
    label = "Glisser-déposer"
    category = "Souris"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("x1", "X départ", "int", 0),
            ParamSpec("y1", "Y départ", "int", 0),
            ParamSpec("x2", "X arrivée", "int", 0),
            ParamSpec("y2", "Y arrivée", "int", 0),
            ParamSpec("duration", "Durée (s)", "float", 0.5, min_value=0.0),
            ParamSpec("button", "Bouton", "choice", "left",
                      choices=["left", "right", "middle"]),
        ]

    def validate(self) -> None:
        for name in ("x1", "y1", "x2", "y2"):
            self._require_number(name)
        if self._require_number("duration") < 0:
            raise ValueError("La durée ne peut pas être négative.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        # On redresse au cas où (sécurité exécution).
        duration = max(0.0, float(self.params.get("duration", 0.5)))
        return inputs.drag_to(
            int(self.params["x1"]),
            int(self.params["y1"]),
            int(self.params["x2"]),
            int(self.params["y2"]),
            duration=duration,
            button=str(self.params.get("button", "left")),
        )

    def summary(self) -> str:
        return (
            f"Glisser ({self.params.get('x1')}, {self.params.get('y1')}) → "
            f"({self.params.get('x2')}, {self.params.get('y2')})"
        )
