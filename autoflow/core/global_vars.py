"""Variables **globales** partagées entre workflows (persistées en JSON).

Contrairement au :class:`VariableStore` (propre à une exécution), ces variables
survivent et sont communes à tous les workflows. Stockage simple dans le dossier
de données utilisateur — **aucun serveur**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class GlobalVariables:
    """Magasin de variables globales persistées dans un fichier JSON."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path is not None else _default_path()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # -- Accès -------------------------------------------------------------
    def get(self, name: str, default: Any = None) -> Any:
        return self._data.get(str(name), default)

    def set(self, name: str, value: Any) -> None:
        self._data[str(name)] = value
        self._save()

    def delete(self, name: str) -> None:
        if str(name) in self._data:
            del self._data[str(name)]
            self._save()

    def all(self) -> dict[str, Any]:
        return dict(self._data)


def _default_path() -> Path:
    from ..persistence import store
    return store.data_dir() / "global_vars.json"
