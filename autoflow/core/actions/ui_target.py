"""Action de ciblage d'élément d'interface (UI Automation Windows).

Cliquer / saisir en désignant un **élément par son nom** (bouton, champ…) plutôt
que par des coordonnées fragiles — bien plus fiable. Windows uniquement :
dégradation propre ailleurs (message clair, pas de crash).
"""

from __future__ import annotations

from typing import Any

from ...services import ui_automation
from ..registry import register
from .base import Action, ParamSpec


@register
class UiElementAction(Action):
    """Clique ou saisit du texte dans un élément d'interface ciblé par son nom."""

    type_name = "ui_element"
    label = "Cibler un élément d'interface"
    category = "Souris"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("operation", "Action", "choice", "click",
                      choices=["click", "set_text"]),
            ParamSpec("window", "Fenêtre", "window", "", supports_vars=True,
                      placeholder="Ex : Calculatrice"),
            ParamSpec("name", "Nom de l'élément", "str", "", supports_vars=True,
                      placeholder="Ex : Égale"),
            ParamSpec("control_type", "Type d'élément (optionnel)", "str", "",
                      placeholder="Ex : Button, Edit"),
            ParamSpec("text", "Texte à saisir", "text", "", supports_vars=True,
                      depends_on=("operation", "set_text")),
        ]

    def validate(self) -> None:
        if not str(self.params.get("name", "")).strip():
            raise ValueError("Le nom de l'élément ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        backend = (context or {}).get("ui_backend")  # injection pour tests
        log = (context or {}).get("log")
        if not ui_automation.is_available(backend):
            if callable(log):
                log("Ciblage d'éléments d'interface indisponible sur ce système.",
                    "warning")
            return False
        window = str(self._resolve(self.params.get("window", ""), context))
        name = str(self._resolve(self.params.get("name", ""), context))
        ctype = str(self.params.get("control_type", "")).strip()
        try:
            if str(self.params.get("operation", "click")) == "set_text":
                text = str(self._resolve(self.params.get("text", ""), context))
                return ui_automation.set_text(window, name, text, ctype, backend=backend)
            return ui_automation.click_element(window, name, ctype, backend=backend)
        except ui_automation.UiAutomationUnavailable as exc:
            if callable(log):
                log(f"Ciblage UI indisponible : {exc}", "warning")
            return False

    def summary(self) -> str:
        op = "Saisir dans" if self.params.get("operation") == "set_text" else "Cliquer sur"
        return f"{op} l'élément « {self.params.get('name')} »"
