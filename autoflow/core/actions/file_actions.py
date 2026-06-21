"""Actions sur fichiers & dossiers : créer, copier, déplacer, supprimer, lire,
écrire/ajouter du texte. Chemins concrets, support des ``{{variables}}``.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..registry import register
from .base import Action, ParamSpec

FILE_OPERATIONS = {
    "create_folder": "Créer un dossier",
    "copy": "Copier",
    "move": "Déplacer / renommer",
    "delete": "Supprimer",
}


@register
class FileOperationAction(Action):
    """Opération de gestion sur un fichier ou dossier."""

    type_name = "file_operation"
    label = "Fichier / dossier : opération"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("operation", "Opération", "choice", "copy",
                      choices=list(FILE_OPERATIONS.keys())),
            ParamSpec("source", "Chemin source", "file", "", supports_vars=True,
                      placeholder="Ex : C:\\data\\fichier.txt"),
            ParamSpec("destination", "Destination", "file", "", supports_vars=True,
                      depends_on=("operation", ("copy", "move")),
                      placeholder="Ex : C:\\sauvegarde\\fichier.txt"),
            ParamSpec("overwrite", "Écraser si existe", "bool", True,
                      depends_on=("operation", ("copy", "move"))),
        ]

    def validate(self) -> None:
        if not str(self.params.get("source", "")).strip():
            raise ValueError("Le chemin source ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        op = str(self.params.get("operation", "copy"))
        src = Path(str(self._resolve(self.params.get("source", ""), context)))
        dst_raw = str(self._resolve(self.params.get("destination", ""), context))
        dst = Path(dst_raw) if dst_raw else None
        overwrite = bool(self.params.get("overwrite", True))

        if op == "create_folder":
            src.mkdir(parents=True, exist_ok=True)
        elif op == "delete":
            _delete(src)
        elif op in ("copy", "move"):
            if dst is None:
                raise ValueError("La destination est requise pour cette opération.")
            _transfer(op, src, dst, overwrite)
        else:
            raise ValueError(f"Opération de fichier inconnue : {op!r}")

        log = (context or {}).get("log")
        if callable(log):
            log(f"{FILE_OPERATIONS.get(op, op)} : {src}", "info")
        return True

    def summary(self) -> str:
        return f"{FILE_OPERATIONS.get(str(self.params.get('operation')), 'Fichier')} : {self.params.get('source')}"


@register
class ReadFileAction(Action):
    """Lit le contenu texte d'un fichier dans une variable."""

    type_name = "read_file"
    label = "Lire un fichier texte"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Fichier à lire", "file", "", supports_vars=True),
            ParamSpec("var_name", "Stocker le contenu dans", "variable", "contenu"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin du fichier ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        path = Path(str(self._resolve(self.params.get("path", ""), context)))
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        store = (context or {}).get("variables")
        var = str(self.params.get("var_name", "")).strip()
        if store is not None and var:
            store.set(var, content)
        return content

    def summary(self) -> str:
        return f"Lire {self.params.get('path')} → {self.params.get('var_name')}"


@register
class WriteFileAction(Action):
    """Écrit (ou ajoute) du texte dans un fichier."""

    type_name = "write_file"
    label = "Écrire dans un fichier texte"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Fichier de destination", "file", "", supports_vars=True),
            ParamSpec("content", "Contenu", "text", "", supports_vars=True),
            ParamSpec("append", "Ajouter à la suite (sinon écraser)", "bool", False),
            ParamSpec("newline", "Ajouter un saut de ligne", "bool", True),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin du fichier ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        path = Path(str(self._resolve(self.params.get("path", ""), context)))
        content = str(self._resolve(self.params.get("content", ""), context))
        if bool(self.params.get("newline", True)):
            content += "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if bool(self.params.get("append", False)) else "w"
        with path.open(mode, encoding="utf-8") as fh:
            fh.write(content)
        return True

    def summary(self) -> str:
        mode = "ajout" if self.params.get("append") else "écrasement"
        return f"Écrire dans {self.params.get('path')} ({mode})"


def _delete(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def _transfer(op: str, src: Path, dst: Path, overwrite: bool) -> None:
    if dst.exists() and overwrite:
        _delete(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if op == "copy":
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    else:  # move / rename
        shutil.move(str(src), str(dst))
