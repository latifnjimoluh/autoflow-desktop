"""Chargement des polices embarquées (fonctionnement 100 % hors-ligne).

Les fichiers de police (``Inter``, ``JetBrains Mono``) sont chargés depuis
``autoflow/ui/theme/assets/fonts/`` s'ils sont présents. **En leur absence**,
l'app retombe proprement sur les piles système définies dans
:mod:`autoflow.ui.theme.tokens` (``Segoe UI`` / ``Consolas``…) : aucune erreur,
aucune dépendance réseau.

La fonction est **idempotente** et sûre hors écran (renvoie une liste vide si
Qt ou les fichiers manquent).
"""

from __future__ import annotations

from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

_loaded: list[str] | None = None


def load_embedded_fonts() -> list[str]:
    """Charge les polices ``.ttf``/``.otf`` embarquées dans la base Qt.

    Renvoie la liste des familles effectivement chargées (vide si aucune).
    Le résultat est mémorisé : un second appel ne recharge pas.
    """
    global _loaded
    if _loaded is not None:
        return _loaded

    families: list[str] = []
    try:
        from PySide6.QtGui import QFontDatabase
    except Exception:  # noqa: BLE001
        _loaded = families
        return families

    if FONTS_DIR.is_dir():
        for path in sorted(FONTS_DIR.glob("*")):
            if path.suffix.lower() not in (".ttf", ".otf"):
                continue
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id >= 0:
                families.extend(QFontDatabase.applicationFontFamilies(font_id))

    _loaded = families
    return families
