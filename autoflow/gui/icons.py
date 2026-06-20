"""Icônes (emoji) par catégorie, type d'action et **état d'exécution**.

Centralise les pictogrammes utilisés par la palette, la vue en nœuds et la liste
d'actions, pour une lecture immédiate par un utilisateur non technique. Les
**couleurs de catégorie** proviennent des tokens de design (source unique), de
sorte que les liserés de nœuds restent cohérents avec le thème.

Les icônes d'état (succès, erreur, en cours, en pause) ne s'appuient **jamais**
sur la seule couleur : chaque état combine un glyphe distinct et un libellé,
pour rester accessible (daltonisme).
"""

from __future__ import annotations

from ..ui.theme import category_color as _category_color

CATEGORY_ICONS = {
    "Clavier": "⌨",
    "Souris": "🖱",
    "Fenêtres": "🪟",
    "Système": "⚙",
    "Contrôle": "🔀",
    "Variables": "📦",
    "Écran": "🖥",
    "Général": "▫",
}

ACTION_ICONS = {
    "key_press": "⌨",
    "hotkey": "⌨",
    "type_text": "📝",
    "click": "🖱",
    "move_mouse": "🖱",
    "drag": "✋",
    "scroll": "🖱",
    "activate_window": "🪟",
    "launch_app": "🚀",
    "wait_for_window": "⏳",
    "run_command": "⚙",
    "clipboard_set": "📋",
    "clipboard_get": "📋",
    "clipboard_paste": "📋",
    "condition": "🔀",
    "loop": "🔁",
    "wait": "⏱",
    "run_workflow": "🧩",
    "set_variable": "📦",
    "increment_variable": "➕",
    "screenshot": "📸",
    "find_image": "🔍",
    "wait_for_image": "⏳",
    "click_image": "🖼",
    "wait_for_pixel": "🎨",
    "read_text": "🔡",
}


# Icônes d'état d'exécution : (glyphe, libellé, clé sémantique de token).
STATE_ICONS = {
    "idle": ("○", "Prêt", "muted"),
    "running": ("⏵", "En cours", "info"),
    "paused": ("⏸", "En pause", "warning"),
    "success": ("✔", "Succès", "success"),
    "error": ("✖", "Erreur", "error"),
}


def category_icon(category: str) -> str:
    """Renvoie l'icône d'une catégorie (repli générique)."""
    return CATEGORY_ICONS.get(category, "▫")


def action_icon(type_name: str, category: str = "Général") -> str:
    """Renvoie l'icône d'un type d'action (repli sur l'icône de catégorie)."""
    return ACTION_ICONS.get(type_name) or category_icon(category)


def category_color(category: str) -> str:
    """Couleur (liseré) d'une catégorie, issue des tokens de design."""
    return _category_color(category)


def state_icon(state: str) -> tuple[str, str, str]:
    """Renvoie ``(glyphe, libellé, clé_token)`` pour un état (repli ``idle``)."""
    return STATE_ICONS.get(state, STATE_ICONS["idle"])
