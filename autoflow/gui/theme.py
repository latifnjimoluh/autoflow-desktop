"""Pont de compatibilité vers le **système de design v4** (``autoflow.ui.theme``).

Historiquement, ce module portait les palettes et le QSS. Ils vivent désormais
dans :mod:`autoflow.ui.theme` (tokens = source unique de vérité, ``ThemeManager``,
QSS généré). Ce fichier ne conserve que :

- :func:`apply_theme` / :func:`palette` / :func:`current_theme` — délèguent au
  ``ThemeManager`` global et restent l'API utilisée par ``gui/``.
- :func:`tr` et le dictionnaire d'i18n (FR/EN) — purement interface.

Aucune couleur n'est codée ici : tout provient des tokens.
"""

from __future__ import annotations

from typing import Any

from ..ui.theme import manager as _manager
from ..ui.theme import resolve as _resolve


def palette(theme: str | None = None) -> dict[str, str]:
    """Renvoie la palette plate de tokens (thème courant si ``theme`` est ``None``).

    Conserve les clés héritées (``window``, ``accent_pressed``, ``danger``…) en
    plus des nouvelles, pour les widgets peints à la main.
    """
    if theme is None:
        theme = _manager().current
    return _resolve(theme)


def current_theme() -> str:
    """Nom du thème actuellement appliqué (``dark`` / ``light``)."""
    return _manager().current


def apply_theme(app: Any, theme: str = "dark") -> None:
    """Applique le thème à l'application via le ``ThemeManager`` global."""
    mgr = _manager()
    mgr.attach(app)
    mgr.apply(theme)


# -- Internationalisation légère (FR par défaut, EN alternatif) ------------
_STRINGS = {
    "fr": {
        "start": "▶ Démarrer", "pause": "⏸ Pause", "stop": "⏹ Arrêter",
        "save": "💾 Enregistrer", "settings": "⚙ Réglages",
        "history": "📊 Historique", "step": "⏭ Étape", "export_py": "🐍 Export .py",
        "ready": "Prêt", "running": "En cours", "paused": "En pause",
        "stopped": "Arrêté", "show": "Afficher", "quit": "Quitter",
        "profile": "Profil", "about": "À propos", "toggle_theme": "🌓 Thème",
    },
    "en": {
        "start": "▶ Start", "pause": "⏸ Pause", "stop": "⏹ Stop",
        "save": "💾 Save", "settings": "⚙ Settings",
        "history": "📊 History", "step": "⏭ Step", "export_py": "🐍 Export .py",
        "ready": "Ready", "running": "Running", "paused": "Paused",
        "stopped": "Stopped", "show": "Show", "quit": "Quit",
        "profile": "Profile", "about": "About", "toggle_theme": "🌓 Theme",
    },
}


def tr(key: str, lang: str = "fr") -> str:
    """Traduit une clé d'interface dans la langue choisie (repli FR)."""
    table = _STRINGS.get(lang, _STRINGS["fr"])
    return table.get(key, _STRINGS["fr"].get(key, key))
