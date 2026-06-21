"""Coffre de secrets **chiffré** (fichier local, aucun serveur).

Chiffrement symétrique **Fernet** (`cryptography`). La clé est stockée à part
dans le dossier de données utilisateur (permissions restreintes au mieux). Les
valeurs sensibles (clés d'API, identifiants SMTP…) ne sont **jamais** écrites en
clair dans les workflows : on n'y référence qu'un **nom de secret**.

``cryptography`` est importé **paresseusement** : son absence lève un message
clair seulement à l'usage, sans empêcher le reste de l'app de démarrer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SecretsError(RuntimeError):
    """Erreur liée au coffre de secrets (chiffrement indisponible, etc.)."""


class SecretVault:
    """Coffre clé→valeur chiffré sur disque."""

    def __init__(self, path: str | Path | None = None,
                 key_path: str | Path | None = None) -> None:
        self._path = Path(path) if path is not None else _default_vault_path()
        self._key_path = (Path(key_path) if key_path is not None
                          else self._path.with_suffix(".key"))

    # -- Clé ---------------------------------------------------------------
    def _fernet(self):
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:  # pragma: no cover - dépend de l'environnement
            raise SecretsError(
                "Le coffre de secrets nécessite « cryptography ».") from exc
        if self._key_path.exists():
            key = self._key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self._key_path.parent.mkdir(parents=True, exist_ok=True)
            self._key_path.write_bytes(key)
            _restrict(self._key_path)
        return Fernet(key)

    # -- Stockage chiffré --------------------------------------------------
    def _read_all(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        token = self._path.read_bytes()
        if not token:
            return {}
        try:
            raw = self._fernet().decrypt(token)
        except Exception as exc:  # noqa: BLE001 — token corrompu/clé changée
            raise SecretsError("Coffre illisible (clé manquante ou corrompue).") from exc
        return json.loads(raw.decode("utf-8"))

    def _write_all(self, data: dict[str, str]) -> None:
        token = self._fernet().encrypt(json.dumps(data).encode("utf-8"))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(token)
        _restrict(self._path)

    # -- API ---------------------------------------------------------------
    def set(self, name: str, value: str) -> None:
        """Enregistre (chiffré) un secret."""
        data = self._read_all()
        data[str(name)] = str(value)
        self._write_all(data)

    def get(self, name: str, default: Any = None) -> Any:
        """Renvoie un secret déchiffré (ou ``default`` si absent)."""
        return self._read_all().get(str(name), default)

    def delete(self, name: str) -> None:
        data = self._read_all()
        if str(name) in data:
            del data[str(name)]
            self._write_all(data)

    def names(self) -> list[str]:
        """Liste les **noms** de secrets (jamais les valeurs)."""
        return sorted(self._read_all().keys())


def _restrict(path: Path) -> None:
    """Restreint les permissions du fichier (best-effort, multi-OS)."""
    try:
        import os
        import stat
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:  # pragma: no cover - selon l'OS/les droits
        pass


def _default_vault_path() -> Path:
    from ..persistence import store
    return store.data_dir() / "secrets.vault"
