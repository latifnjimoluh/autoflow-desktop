"""Action : appui sur une touche."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class KeyPressAction(Action):
    """Appuie une ou plusieurs fois sur une touche unique (``enter``, ``f5``…)."""

    type_name = "key_press"
    label = "Appui touche"
    category = "Clavier"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("key", "Touche", "str", "enter",
                      help="Nom de la touche : enter, tab, esc, f5, space…"),
            ParamSpec("presses", "Répétitions", "int", 1),
            ParamSpec("interval", "Intervalle (s)", "float", 0.0),
        ]

    def validate(self) -> None:
        if not str(self.params.get("key", "")).strip():
            raise ValueError("La touche ne peut pas être vide.")
        if int(self.params.get("presses", 1)) < 1:
            raise ValueError("Le nombre de répétitions doit être au moins 1.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        return inputs.press(
            str(self.params["key"]).strip().lower(),
            presses=int(self.params.get("presses", 1)),
            interval=float(self.params.get("interval", 0.0)),
        )

    def summary(self) -> str:
        presses = int(self.params.get("presses", 1))
        suffixe = f" ×{presses}" if presses > 1 else ""
        return f"Touche '{self.params.get('key')}'{suffixe}"
