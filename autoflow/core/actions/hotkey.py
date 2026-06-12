"""Action : raccourci clavier (combinaison de touches)."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class HotkeyAction(Action):
    """Appuie simultanément sur une combinaison de touches (``ctrl+end``…)."""

    type_name = "hotkey"
    label = "Raccourci clavier"
    category = "Clavier"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("keys", "Raccourci", "hotkey", ["ctrl", "c"],
                      placeholder="Ex : Ctrl + Maj + S",
                      help="Cliquez « Enregistrer » puis pressez la combinaison, "
                           "ou cochez les modificateurs et choisissez la touche."),
        ]

    def _keys(self) -> list[str]:
        keys = self.params.get("keys", [])
        if isinstance(keys, str):
            # Tolère une saisie "ctrl+end" ou "ctrl, end".
            keys = [k.strip() for k in keys.replace(",", "+").split("+")]
        return [str(k).strip().lower() for k in keys if str(k).strip()]

    def validate(self) -> None:
        if not self._keys():
            raise ValueError("Le raccourci doit comporter au moins une touche.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        return inputs.hotkey(self._keys())

    def summary(self) -> str:
        from ...services.keys import keys_to_label

        return "Raccourci clavier « " + keys_to_label(self._keys()) + " »"
