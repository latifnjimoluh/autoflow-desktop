"""Action : attente de l'apparition d'une fenêtre."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class WaitForWindowAction(Action):
    """Attend qu'une fenêtre dont le titre correspond apparaisse (avec timeout)."""

    type_name = "wait_for_window"
    label = "Attendre une fenêtre"
    category = "Fenêtres"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("title", "Fenêtre attendue", "window", "",
                      placeholder="Ex : Calculatrice",
                      help="Choisissez une fenêtre ouverte ou saisissez un "
                           "fragment de titre à attendre."),
            ParamSpec("match", "Correspondance du titre", "choice", "contains",
                      choices=["contains", "exact"]),
            ParamSpec("timeout", "Délai maximum d'attente (s)", "float", 10.0, min_value=0.1),
        ]

    def validate(self) -> None:
        if not str(self.params.get("title", "")).strip():
            raise ValueError("Le titre de la fenêtre ne peut pas être vide.")
        if self._require_number("timeout") <= 0:
            raise ValueError("Le délai d'attente doit être positif.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        # On redresse au cas où (sécurité exécution).
        timeout = max(0.1, float(self.params.get("timeout", 10.0)))
        found = windows.wait_for_window(
            title=str(self.params["title"]),
            match=str(self.params.get("match", "contains")),
            timeout=timeout,
            sleep=(context or {}).get("sleep"),
        )
        if not found:
            log = (context or {}).get("log")
            if callable(log):
                log(f"Fenêtre '{self.params['title']}' non apparue (timeout).",
                    "warning")
        return found

    def summary(self) -> str:
        return f"Attendre la fenêtre « {self.params.get('title')} »"
