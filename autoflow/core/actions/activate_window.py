"""Action : activation d'une fenêtre par son titre."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class ActivateWindowAction(Action):
    """Recherche une fenêtre par titre et la met au premier plan.

    Reproduit le cœur des deux scripts d'origine : ciblage par titre puis
    passage au premier plan, avec l'option ``force_foreground`` qui applique la
    technique ctypes (simulation Alt) contournant le « Access Denied » Windows.
    """

    type_name = "activate_window"
    label = "Activer une fenêtre"
    category = "Fenêtres"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("title", "Titre", "str", "",
                      help="Titre (ou fragment) de la fenêtre cible."),
            ParamSpec("match", "Correspondance", "choice", "contains",
                      choices=["contains", "exact"]),
            ParamSpec("force_foreground", "Forcer le premier plan", "bool", False,
                      help="Astuce Windows (Alt) pour vaincre le refus d'activation."),
        ]

    def validate(self) -> None:
        if not str(self.params.get("title", "")).strip():
            raise ValueError("Le titre de la fenêtre ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        found = windows.activate(
            title=str(self._resolve(self.params["title"], context)),
            match=str(self.params.get("match", "contains")),
            force_foreground=bool(self.params.get("force_foreground", False)),
        )
        if not found:
            log = (context or {}).get("log")
            if callable(log):
                log(f"Fenêtre '{self.params['title']}' introuvable, ouvrez-la.",
                    "warning")
        return found

    def summary(self) -> str:
        suffixe = " [premier plan forcé]" if self.params.get("force_foreground") else ""
        return f"Activer la fenêtre « {self.params.get('title')} »{suffixe}"
