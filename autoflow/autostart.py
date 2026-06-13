"""Démarrage automatique avec Windows via la clé de registre ``Run``.

Utilise le module standard :mod:`winreg` (Windows uniquement). Sur les autres
systèmes, les fonctions se comportent en « no-op » sûr (jamais de crash).
"""

from __future__ import annotations

import sys

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "AutoFlow"


def is_windows() -> bool:
    """Indique si l'on tourne sous Windows."""
    return sys.platform.startswith("win")


def _command(extra: str = "") -> str:
    """Construit la commande de lancement (exécutable gelé ou module Python)."""
    if getattr(sys, "frozen", False):  # exécutable PyInstaller
        base = f'"{sys.executable}"'
    else:
        base = f'"{sys.executable}" -m autoflow.main'
    return f"{base} {extra}".strip()


def enable(extra: str = "") -> bool:
    """Active le démarrage automatique. Renvoie ``True`` en cas de succès."""
    if not is_windows():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _command(extra))
        return True
    except OSError:
        return False


def disable() -> bool:
    """Désactive le démarrage automatique."""
    if not is_windows():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _APP_NAME)
        return True
    except FileNotFoundError:
        return True  # déjà absent
    except OSError:
        return False


def is_enabled() -> bool:
    """Indique si le démarrage automatique est actif."""
    if not is_windows():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, _APP_NAME)
        return True
    except OSError:
        return False
