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
            ParamSpec("text", "Texte à taper", "text", "", supports_vars=True,
                      placeholder="Ex : Bonjour {{date}}",
                      help="Vous pouvez insérer des variables avec {{nom}}."),
            ParamSpec("paste", "Coller d'un coup (plus rapide)", "bool", False,
                      help="Colle le texte instantanément au lieu de le taper "
                           "caractère par caractère."),
            ParamSpec("interval", "Vitesse : intervalle entre caractères (s)",
                      "float", 0.0, depends_on=("paste", False), min_value=0.0),
        ]

    def validate(self) -> None:
        try:
            val = float(self.params.get("interval", 0.0))
            if val < 0:
                raise ValueError(f"L'intervalle ne peut pas être négatif ({val}).")
        except (TypeError, ValueError):
            raise ValueError("L'intervalle doit être un nombre valide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        # On valide, mais on redresse au cas où (sécurité exécution).
        text = str(self._resolve(self.params.get("text", ""), context))
        interval = max(0.0, float(self.params.get("interval", 0.0)))

        if self.params.get("paste"):
            clip = (context or {}).get("clipboard")
            if clip is not None:
                clip.set_text(text)
                return inputs.hotkey(["ctrl", "v"])
        return inputs.type_text(
            text,
            interval=interval,
        )

    def summary(self) -> str:
        text = str(self.params.get("text", ""))
        court = text if len(text) <= 30 else text[:27] + "…"
        return f"Taper « {court} »"
