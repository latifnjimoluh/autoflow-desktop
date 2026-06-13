"""Thèmes (clair/sombre) et internationalisation légère (FR/EN)."""

from __future__ import annotations

from typing import Any

_DARK_QSS = """
QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QListWidget,
QTableWidget, QTextEdit {
    background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #3c3c3c;
}
QPushButton, QToolButton {
    background-color: #3c3f41; border: 1px solid #4c4c4c; padding: 4px 8px;
}
QPushButton:hover, QToolButton:hover { background-color: #4c5052; }
QTabBar::tab { background: #3c3f41; padding: 6px; }
QTabBar::tab:selected { background: #2b2b2b; }
QHeaderView::section { background-color: #3c3f41; color: #e0e0e0; }
"""

_LIGHT_QSS = """
QWidget { background-color: #f5f5f5; color: #202020; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QListWidget,
QTableWidget, QTextEdit {
    background-color: #ffffff; color: #202020; border: 1px solid #c0c0c0;
}
QPushButton, QToolButton {
    background-color: #e8e8e8; border: 1px solid #c0c0c0; padding: 4px 8px;
}
QPushButton:hover, QToolButton:hover { background-color: #dcdcdc; }
"""

# Dictionnaire de traduction minimal (FR par défaut, EN en alternative).
_STRINGS = {
    "fr": {
        "start": "▶ Démarrer", "pause": "⏸ Pause", "stop": "⏹ Arrêter",
        "save": "💾 Enregistrer", "settings": "⚙ Réglages",
        "history": "📊 Historique", "step": "⏭ Étape", "export_py": "🐍 Export .py",
        "ready": "Prêt", "running": "En cours", "paused": "En pause",
        "stopped": "Arrêté", "show": "Afficher", "quit": "Quitter",
        "profile": "Profil",
    },
    "en": {
        "start": "▶ Start", "pause": "⏸ Pause", "stop": "⏹ Stop",
        "save": "💾 Save", "settings": "⚙ Settings",
        "history": "📊 History", "step": "⏭ Step", "export_py": "🐍 Export .py",
        "ready": "Ready", "running": "Running", "paused": "Paused",
        "stopped": "Stopped", "show": "Show", "quit": "Quit",
        "profile": "Profile",
    },
}


def tr(key: str, lang: str = "fr") -> str:
    """Traduit une clé d'interface dans la langue choisie (repli FR)."""
    table = _STRINGS.get(lang, _STRINGS["fr"])
    return table.get(key, _STRINGS["fr"].get(key, key))


def apply_theme(app: Any, theme: str = "dark") -> None:
    """Applique la feuille de style correspondant au thème à l'application."""
    app.setStyleSheet(_DARK_QSS if theme == "dark" else _LIGHT_QSS)
