"""Services sous-jacents alimentant les composants concrets de l'interface.

Ces services fournissent la *logique* nécessaire aux widgets guidés (liste des
fenêtres ouvertes, applications installées, capture de touches, exécution isolée
d'une action). Ils sont **mockables** et **testables sans écran** : toute
dépendance liée à l'affichage est importée paresseusement.
"""

from __future__ import annotations

from .apps import AppInfo, list_installed_apps
from .keys import (
    ALL_KEYS,
    KEY_CATEGORIES,
    combo_to_keys,
    keys_to_label,
    normalize_key,
    pynput_to_name,
)
from .test_action import TestResult, test_action
from .windows_list import WindowInfo, list_open_windows

__all__ = [
    "AppInfo",
    "list_installed_apps",
    "ALL_KEYS",
    "KEY_CATEGORIES",
    "combo_to_keys",
    "keys_to_label",
    "normalize_key",
    "pynput_to_name",
    "TestResult",
    "test_action",
    "WindowInfo",
    "list_open_windows",
]
