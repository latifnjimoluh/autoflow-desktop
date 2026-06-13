"""Action : saisie de texte."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class TypeTextAction(Action):
    """Tape une chaîne de caractères, avec intervalle optionnel entre touches."""

    type_name = "type_text"
    label = "Taper du texte"
    category = "Clavier"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("text", "Texte", "text", ""),
            ParamSpec("interval", "Intervalle entre caractères (s)", "float", 0.0),
        ]

    def validate(self) -> None:
        if float(self.params.get("interval", 0.0)) < 0:
            raise ValueError("L'intervalle ne peut pas être négatif.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        return inputs.type_text(
            str(self.params.get("text", "")),
            interval=float(self.params.get("interval", 0.0)),
        )

    def summary(self) -> str:
        text = str(self.params.get("text", ""))
        court = text if len(text) <= 30 else text[:27] + "…"
        return f"Taper « {court} »"
