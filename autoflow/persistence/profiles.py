"""Profils / espaces de travail : regroupement de workflows par contexte.

Chaque profil (« Travail », « Jeux »…) possède son propre dossier de workflows.
Stockage simple sur disque, sous le dossier de données utilisateur.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .store import data_dir, slugify

DEFAULT_PROFILE = "Défaut"


def profiles_root() -> Path:
    """Renvoie (et crée) le dossier racine des profils."""
    path = data_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profile_dir(name: str) -> Path:
    """Renvoie (et crée) le dossier d'un profil."""
    path = profiles_root() / slugify(name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def profile_workflows_dir(name: str) -> Path:
    """Renvoie (et crée) le dossier des workflows d'un profil."""
    path = profile_dir(name) / "workflows"
    path.mkdir(parents=True, exist_ok=True)
    # Conserve le nom affichable du profil.
    label = profile_dir(name) / "name.txt"
    if not label.exists():
        label.write_text(name, encoding="utf-8")
    return path


def list_profiles() -> list[str]:
    """Liste les profils existants (crée le profil par défaut si nécessaire)."""
    root = profiles_root()
    if not any(root.iterdir()):
        profile_workflows_dir(DEFAULT_PROFILE)
    noms = []
    for sous in sorted(root.iterdir()):
        if sous.is_dir():
            label = sous / "name.txt"
            noms.append(label.read_text(encoding="utf-8").strip()
                        if label.exists() else sous.name)
    return noms or [DEFAULT_PROFILE]


def create_profile(name: str) -> Path:
    """Crée un profil et renvoie son dossier de workflows."""
    return profile_workflows_dir(name)


def delete_profile(name: str) -> bool:
    """Supprime un profil (refuse de supprimer le dernier restant)."""
    if len(list_profiles()) <= 1:
        return False
    target = profiles_root() / slugify(name)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
        return True
    return False
