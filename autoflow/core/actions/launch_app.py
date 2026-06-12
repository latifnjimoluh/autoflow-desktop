"""Action : lancement d'une application ou d'un fichier."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class LaunchAppAction(Action):
    """Lance un exécutable ou ouvre un fichier via le système d'exploitation."""

    type_name = "launch_app"
    label = "Lancer une application"
    category = "Fenêtres"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Application", "app", "",
                      placeholder="Ex : notepad.exe",
                      help="Choisissez parmi les applications installées, "
                           "parcourez un fichier, ou saisissez un chemin/commande."),
            ParamSpec("args", "Arguments (optionnel)", "str", "",
                      placeholder="Ex : mon_fichier.txt",
                      help="Arguments séparés par des espaces."),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin de l'application ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        raw_args = str(self.params.get("args", "")).strip()
        args = raw_args.split() if raw_args else []
        return windows.launch(str(self.params["path"]), args)

    def summary(self) -> str:
        from pathlib import Path

        path = str(self.params.get("path", ""))
        nom = Path(path).stem or path or "?"
        return f"Lancer l'application « {nom} »"
