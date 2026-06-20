"""Système de design AutoFlow — tokens, QSS, gestionnaire de thème.

Point d'entrée unique de la couche visuelle. Réexporte l'essentiel :

- :data:`tokens` — la source unique de vérité (couleurs, type, espacement…).
- :func:`resolve` — tokens plats d'un thème.
- :class:`ThemeManager` / :func:`manager` — application et bascule à chaud.
- :func:`build_qss` — génération de la feuille de style.
- :func:`apply_elevation` — ombres douces (élévation).
"""

from __future__ import annotations

from . import tokens
from .elevation import apply_elevation
from .fonts import load_embedded_fonts
from .manager import ThemeManager, manager, qss_for
from .qss import build_qss
from .tokens import category_color, resolve

__all__ = [
    "tokens",
    "resolve",
    "category_color",
    "build_qss",
    "qss_for",
    "ThemeManager",
    "manager",
    "apply_elevation",
    "load_embedded_fonts",
]
