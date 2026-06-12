"""Action : clic de souris."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class ClickAction(Action):
    """Effectue un clic (simple ou double) à des coordonnées ou sur place."""

    type_name = "click"
    label = "Clic"
    category = "Souris"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("use_current", "Cliquer à la position actuelle de la souris",
                      "bool", False,
                      help="Si coché, ignore X/Y et clique là où se trouve le curseur."),
            ParamSpec("x", "X", "int", 0, depends_on=("use_current", False),
                      help="Utilisez « Capturer une position » pour pointer à l'écran."),
            ParamSpec("y", "Y", "int", 0, depends_on=("use_current", False)),
            ParamSpec("button", "Bouton de la souris", "choice", "left",
                      choices=["left", "right", "middle"]),
            ParamSpec("clicks", "Nombre de clics", "int", 1,
                      help="1 = simple clic, 2 = double clic."),
        ]

    def validate(self) -> None:
        if int(self.params.get("clicks", 1)) < 1:
            raise ValueError("Le nombre de clics doit être au moins 1.")
        if not self.params.get("use_current"):
            self._require_number("x")
            self._require_number("y")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        use_current = bool(self.params.get("use_current"))
        x = None if use_current else int(self.params["x"])
        y = None if use_current else int(self.params["y"])
        return inputs.click(
            x=x,
            y=y,
            button=str(self.params.get("button", "left")),
            clicks=int(self.params.get("clicks", 1)),
        )

    _BUTTONS = {"left": "gauche", "right": "droit", "middle": "du milieu"}

    def summary(self) -> str:
        clics = "Double-clic" if int(self.params.get("clicks", 1)) >= 2 else "Clic"
        bouton = self._BUTTONS.get(self.params.get("button", "left"), "gauche")
        if self.params.get("use_current"):
            return f"{clics} {bouton} à la position actuelle"
        return f"{clics} {bouton} à la position ({self.params.get('x')}, {self.params.get('y')})"
