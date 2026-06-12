"""Actions système : exécution de commandes et presse-papiers."""

from __future__ import annotations

import subprocess
from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class RunCommandAction(Action):
    """Exécute une commande système et capture sa sortie dans une variable."""

    type_name = "run_command"
    label = "Exécuter une commande"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("command", "Commande / script", "text", "", supports_vars=True,
                      placeholder="Ex : echo Bonjour"),
            ParamSpec("shell", "Via le shell", "bool", True,
                      help="Interprète la commande par le shell du système."),
            ParamSpec("workdir", "Dossier de travail (optionnel)", "folder", "",
                      placeholder="Ex : C:\\mon_projet"),
            ParamSpec("output_var", "Capturer la sortie dans la variable", "variable", "",
                      placeholder="Ex : resultat"),
            ParamSpec("timeout", "Délai maximum (s)", "float", 30.0),
        ]

    def validate(self) -> None:
        if not str(self.params.get("command", "")).strip():
            raise ValueError("La commande ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        command = self._resolve(self.params.get("command", ""), context)
        use_shell = bool(self.params.get("shell", True))
        timeout = float(self.params.get("timeout", 30.0)) or None
        workdir = str(self.params.get("workdir", "")).strip() or None
        result = subprocess.run(
            command if use_shell else command.split(),
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        store = (context or {}).get("variables")
        var = str(self.params.get("output_var", "")).strip()
        if store is not None and var:
            store.set(var, (result.stdout or "").strip())
            store.set(f"{var}_code", result.returncode)
        log = (context or {}).get("log")
        if callable(log):
            log(f"Commande terminée (code {result.returncode}).", "info")
        return result.returncode

    def summary(self) -> str:
        cmd = str(self.params.get("command", ""))
        court = cmd if len(cmd) <= 30 else cmd[:27] + "…"
        return f"Commande : {court}"


@register
class ClipboardSetAction(Action):
    """Écrit du texte dans le presse-papiers."""

    type_name = "clipboard_set"
    label = "Presse-papiers : écrire"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [ParamSpec("text", "Texte à copier", "text", "", supports_vars=True,
                          placeholder="Ex : {{resultat}}")]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        clip = (context or {}).get("clipboard")
        text = self._resolve(self.params.get("text", ""), context)
        if clip is not None:
            clip.set_text(text)
        return text

    def summary(self) -> str:
        return "Copier du texte dans le presse-papiers"


@register
class ClipboardGetAction(Action):
    """Lit le presse-papiers dans une variable."""

    type_name = "clipboard_get"
    label = "Presse-papiers : lire"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [ParamSpec("var_name", "Stocker dans la variable", "variable",
                          "presse_papiers")]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        clip = (context or {}).get("clipboard")
        store = (context or {}).get("variables")
        text = clip.get_text() if clip is not None else ""
        if store is not None and str(self.params.get("var_name", "")).strip():
            store.set(str(self.params["var_name"]).strip(), text)
        return text

    def summary(self) -> str:
        return f"Lire le presse-papiers → {self.params.get('var_name')}"


@register
class ClipboardPasteAction(Action):
    """Colle le presse-papiers (Ctrl+V), après écriture optionnelle d'un texte."""

    type_name = "clipboard_paste"
    label = "Presse-papiers : coller"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [ParamSpec("text", "Texte à coller (optionnel)", "text", "",
                          supports_vars=True)]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        clip = (context or {}).get("clipboard")
        text = self._resolve(self.params.get("text", ""), context)
        if text and clip is not None:
            clip.set_text(text)
        return inputs.hotkey(["ctrl", "v"])

    def summary(self) -> str:
        return "Coller (Ctrl+V)"
