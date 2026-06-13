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
            ParamSpec("keys", "Touches", "keys", ["ctrl", "c"],
                      help="Liste des touches du raccourci, ex. ctrl + end."),
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
        return "Raccourci " + "+".join(self._keys())
