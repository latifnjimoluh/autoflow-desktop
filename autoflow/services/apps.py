"""Détection des applications installées (pour le sélecteur « Lancer une app »).

Sous **Windows**, on parcourt les raccourcis ``.lnk`` du menu Démarrer (tous
utilisateurs + utilisateur courant). Hors Windows, on cherche quelques
exécutables courants dans le ``PATH``. Les racines de recherche sont injectables,
ce qui rend la détection **entièrement testable** sans dépendre de la machine.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppInfo:
    """Application détectée : nom lisible + chemin à lancer."""

    name: str
    path: str

    def __str__(self) -> str:  # pragma: no cover - confort d'affichage
        return self.name


def _start_menu_roots() -> list[Path]:
    """Renvoie les dossiers du menu Démarrer Windows (peuvent ne pas exister)."""
    import os

    roots: list[Path] = []
    program_data = os.environ.get("PROGRAMDATA")
    appdata = os.environ.get("APPDATA")
    if program_data:
        roots.append(Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    if appdata:
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return roots


def list_installed_apps(
    roots: list[Path] | None = None,
    *,
    is_windows: bool | None = None,
    path_lookup: bool = True,
) -> list[AppInfo]:
    """Renvoie la liste des applications détectées, triée par nom, dédupliquée.

    Args:
        roots : dossiers à explorer (par défaut : menu Démarrer sous Windows).
            Injectable pour les tests.
        is_windows : force le mode Windows (par défaut : auto-détecté).
        path_lookup : hors Windows, cherche aussi des exécutables courants du PATH.
    """
    windows = sys.platform.startswith("win") if is_windows is None else is_windows
    search_roots = roots if roots is not None else (_start_menu_roots() if windows else [])

    found: dict[str, AppInfo] = {}
    for root in search_roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for shortcut in sorted(root.rglob("*.lnk")):
            name = shortcut.stem
            if name and name.lower() not in found:
                found[name.lower()] = AppInfo(name=name, path=str(shortcut))

    if not windows and path_lookup and roots is None:
        for app in _common_unix_apps():
            if app.name.lower() not in found:
                found[app.name.lower()] = app

    return sorted(found.values(), key=lambda a: a.name.lower())


def _common_unix_apps() -> list[AppInfo]:
    """Cherche quelques applications courantes dans le ``PATH`` (hors Windows)."""
    import shutil

    candidates = {
        "Firefox": "firefox",
        "Google Chrome": "google-chrome",
        "Chromium": "chromium",
        "Terminal": "x-terminal-emulator",
        "Éditeur de texte": "gedit",
        "VS Code": "code",
        "Bloc-notes (gedit)": "gedit",
    }
    apps: list[AppInfo] = []
    for label, exe in candidates.items():
        resolved = shutil.which(exe)
        if resolved:
            apps.append(AppInfo(name=label, path=resolved))
    return apps
