"""Thèmes (clair/sombre) modernes et internationalisation légère (FR/EN).

Le style est généré à partir d'une **palette** par thème, ce qui garantit la
cohérence entre le mode clair et le mode sombre et facilite les retouches. Le
rendu vise une esthétique soignée (surfaces, coins arrondis, couleur d'accent,
états *hover/focus/pressed*) plutôt qu'un QSS plat.
"""

from __future__ import annotations

from typing import Any

# -- Palettes -------------------------------------------------------------
_DARK = {
    "window": "#1c1d24",      # fond général
    "surface": "#24262f",     # panneaux
    "surface_alt": "#2b2e38",  # champs, éléments
    "elevated": "#31343f",    # survol / éléments hauts
    "border": "#383b47",
    "border_strong": "#454956",
    "text": "#e7e9f0",
    "muted": "#9aa0b2",
    "accent": "#6c8cff",
    "accent_hover": "#809cff",
    "accent_pressed": "#5a78e6",
    "accent_text": "#ffffff",
    "selection": "#34507f",
    "danger": "#e5534b",
    "success": "#3fb950",
}

_LIGHT = {
    "window": "#eef1f6",
    "surface": "#ffffff",
    "surface_alt": "#f6f8fb",
    "elevated": "#eaeef5",
    "border": "#d8dde7",
    "border_strong": "#c2c9d6",
    "text": "#1b1e28",
    "muted": "#697086",
    "accent": "#4361ee",
    "accent_hover": "#3551db",
    "accent_pressed": "#2c46c2",
    "accent_text": "#ffffff",
    "selection": "#cfe0ff",
    "danger": "#d64541",
    "success": "#2f9e44",
}


def _build_qss(p: dict[str, str]) -> str:
    """Construit la feuille de style complète à partir d'une palette."""
    return f"""
* {{
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 13px;
    outline: none;
}}
QWidget {{
    background-color: {p['window']};
    color: {p['text']};
}}
QMainWindow, QDialog {{ background-color: {p['window']}; }}

/* --- Conteneurs : panneaux, splitter --- */
QSplitter::handle {{ background-color: {p['border']}; }}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical {{ height: 2px; }}

QScrollArea {{ border: none; }}

/* --- Champs de saisie --- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit,
QTextEdit, QAbstractSpinBox {{
    background-color: {p['surface_alt']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 7px;
    padding: 5px 8px;
    selection-background-color: {p['accent']};
    selection-color: {p['accent_text']};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
QPlainTextEdit:hover, QTextEdit:hover {{
    border-color: {p['border_strong']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {p['accent']};
}}
QLineEdit:disabled, QComboBox:disabled {{
    color: {p['muted']}; background-color: {p['surface']};
}}
QComboBox::drop-down {{
    border: none; width: 22px; subcontrol-position: center right;
}}
QComboBox QAbstractItemView {{
    background-color: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 7px;
    selection-background-color: {p['accent']};
    selection-color: {p['accent_text']};
    padding: 4px;
}}

/* --- Boutons --- */
QPushButton {{
    background-color: {p['surface_alt']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 7px;
    padding: 6px 14px;
    min-height: 16px;
}}
QPushButton:hover {{ background-color: {p['elevated']}; border-color: {p['accent']}; }}
QPushButton:pressed {{ background-color: {p['accent_pressed']}; color: {p['accent_text']}; }}
QPushButton:checked {{
    background-color: {p['accent']}; color: {p['accent_text']};
    border-color: {p['accent']};
}}
QPushButton:disabled {{ color: {p['muted']}; border-color: {p['border']}; }}

/* Boutons d'accent (propriété dynamique accent="true") */
QPushButton[accent="true"] {{
    background-color: {p['accent']};
    color: {p['accent_text']};
    border: 1px solid {p['accent']};
    font-weight: 600;
}}
QPushButton[accent="true"]:hover {{ background-color: {p['accent_hover']}; border-color: {p['accent_hover']}; }}
QPushButton[accent="true"]:pressed {{ background-color: {p['accent_pressed']}; }}

QToolButton {{
    background-color: transparent;
    color: {p['text']};
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 5px 9px;
}}
QToolButton:hover {{ background-color: {p['elevated']}; border-color: {p['border_strong']}; }}
QToolButton:pressed, QToolButton:checked {{
    background-color: {p['accent']}; color: {p['accent_text']};
}}
QToolButton::menu-indicator {{ image: none; }}

/* --- Barre d'outils --- */
QToolBar {{
    background-color: {p['surface']};
    border: none;
    border-bottom: 1px solid {p['border']};
    padding: 5px 6px;
    spacing: 4px;
}}
QToolBar QToolButton {{ padding: 6px 10px; }}
QToolBar::separator {{
    background-color: {p['border']}; width: 1px; margin: 5px 6px;
}}

/* --- Onglets --- */
QTabWidget::pane {{
    border: 1px solid {p['border']};
    border-radius: 8px;
    top: -1px;
    background-color: {p['surface']};
}}
QTabBar::tab {{
    background: transparent;
    color: {p['muted']};
    padding: 7px 16px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:hover {{ color: {p['text']}; }}
QTabBar::tab:selected {{
    color: {p['accent']};
    border-bottom: 2px solid {p['accent']};
    font-weight: 600;
}}

/* --- Listes & tableaux --- */
QListWidget, QTreeWidget, QTableWidget, QTableView, QTreeView {{
    background-color: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 4px;
    alternate-background-color: {p['surface_alt']};
}}
QListWidget::item {{ padding: 6px 8px; border-radius: 6px; }}
QListWidget::item:hover {{ background-color: {p['elevated']}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {p['accent']}; color: {p['accent_text']};
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {p['selection']}; color: {p['text']};
}}
QHeaderView::section {{
    background-color: {p['surface_alt']};
    color: {p['muted']};
    border: none;
    border-bottom: 1px solid {p['border']};
    padding: 6px 8px;
    font-weight: 600;
}}

/* --- Cases à cocher --- */
QCheckBox, QRadioButton {{ spacing: 7px; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px; height: 17px;
    border: 1px solid {p['border_strong']};
    border-radius: 4px;
    background-color: {p['surface_alt']};
}}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {p['accent']}; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {p['accent']}; border-color: {p['accent']};
}}

/* --- Barres de défilement --- */
QScrollBar:vertical {{
    background: transparent; width: 11px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {p['border_strong']}; border-radius: 5px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['accent']}; }}
QScrollBar:horizontal {{
    background: transparent; height: 11px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {p['border_strong']}; border-radius: 5px; min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {p['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

/* --- Menus --- */
QMenuBar {{ background-color: {p['surface']}; border-bottom: 1px solid {p['border']}; }}
QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
QMenuBar::item:selected {{ background-color: {p['elevated']}; border-radius: 6px; }}
QMenu {{
    background-color: {p['surface']};
    border: 1px solid {p['border_strong']};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{ padding: 6px 22px 6px 14px; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {p['accent']}; color: {p['accent_text']}; }}
QMenu::separator {{ height: 1px; background: {p['border']}; margin: 5px 8px; }}

/* --- Dock & status bar --- */
QDockWidget {{ titlebar-close-icon: none; }}
QDockWidget::title {{
    background-color: {p['surface']};
    color: {p['muted']};
    padding: 7px 10px;
    border-bottom: 1px solid {p['border']};
    font-weight: 600;
}}
QStatusBar {{
    background-color: {p['surface']};
    color: {p['muted']};
    border-top: 1px solid {p['border']};
}}
QStatusBar::item {{ border: none; }}

/* --- Groupes & séparateurs --- */
QGroupBox {{
    border: 1px solid {p['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: {p['accent']};
    font-weight: 600;
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {p['border']}; }}

/* --- Infobulles & boîtes de dialogue --- */
QToolTip {{
    background-color: {p['elevated']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 6px;
    padding: 5px 8px;
}}
QProgressBar {{
    border: 1px solid {p['border']}; border-radius: 7px;
    background-color: {p['surface_alt']}; text-align: center;
}}
QProgressBar::chunk {{ background-color: {p['accent']}; border-radius: 6px; }}
"""


_DARK_QSS = _build_qss(_DARK)
_LIGHT_QSS = _build_qss(_LIGHT)


def palette(theme: str = "dark") -> dict[str, str]:
    """Renvoie la palette de couleurs du thème (utilisée par certains widgets)."""
    return dict(_DARK if theme == "dark" else _LIGHT)


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
