"""Icônes (emoji) par catégorie et par type d'action.

Centralise les pictogrammes utilisés par la palette, la vue en nœuds et la liste
d'actions, pour une lecture immédiate par un utilisateur non technique.
"""

from __future__ import annotations

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


def category_icon(category: str) -> str:
    """Renvoie l'icône d'une catégorie (repli générique)."""
    return CATEGORY_ICONS.get(category, "▫")


def action_icon(type_name: str, category: str = "Général") -> str:
    """Renvoie l'icône d'un type d'action (repli sur l'icône de catégorie)."""
    return ACTION_ICONS.get(type_name) or category_icon(category)
