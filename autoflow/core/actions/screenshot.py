"""Action : capture d'écran."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class ScreenshotAction(Action):
    """Capture l'écran entier ou une région et l'enregistre dans un fichier."""

    type_name = "screenshot"
    label = "Capture d'écran"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Fichier de sortie", "file", "capture.png"),
            ParamSpec("region", "Région (optionnel)", "bool", False,
                      help="Si coché, capture la zone X/Y/Largeur/Hauteur."),
            ParamSpec("x", "X", "int", 0),
            ParamSpec("y", "Y", "int", 0),
            ParamSpec("width", "Largeur", "int", 0),
            ParamSpec("height", "Hauteur", "int", 0),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin de sortie ne peut pas être vide.")
        if self.params.get("region"):
            for name in ("width", "height"):
                if int(self.params.get(name, 0)) <= 0:
                    raise ValueError("La région doit avoir largeur/hauteur positives.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        region = None
        if self.params.get("region"):
            region = (
                int(self.params["x"]),
                int(self.params["y"]),
                int(self.params["width"]),
                int(self.params["height"]),
            )
        return inputs.screenshot(str(self.params["path"]), region=region)

    def summary(self) -> str:
        portee = "région" if self.params.get("region") else "écran entier"
        return f"Capture ({portee}) → {self.params.get('path')}"
