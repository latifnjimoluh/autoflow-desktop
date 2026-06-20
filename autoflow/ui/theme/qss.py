"""Génération du QSS (feuille de style Qt) à partir des tokens de design.

Une **seule** fonction publique, :func:`build_qss`, transforme un dictionnaire
plat de tokens (voir :mod:`autoflow.ui.theme.tokens`) en feuille de style
complète et cohérente couvrant **tous** les composants et **tous** leurs états
(normal / survol / focus / actif / désactivé).

Contraintes Qt respectées : pas de ``box-shadow`` (élévation via
``QGraphicsDropShadowEffect``), dégradés via ``qlineargradient``, sélecteurs
ciblant ``objectName`` et propriétés dynamiques (``variant``, ``accent``…).
"""

from __future__ import annotations


def build_qss(t: dict[str, str]) -> str:
    """Construit la feuille de style complète depuis le dictionnaire de tokens."""
    return f"""
/* ===================== Base ===================== */
* {{
    font-family: {t['font_sans']};
    font-size: 14px;
    outline: none;
}}
QWidget {{
    background-color: {t['bg']};
    color: {t['text']};
}}
QMainWindow, QDialog {{ background-color: {t['bg']}; }}
QWidget:disabled {{ color: {t['muted']}; }}

QLabel {{ background: transparent; }}
QLabel[variant="display"] {{ font-size: 24px; font-weight: 600; }}
QLabel[variant="title"]   {{ font-size: 20px; font-weight: 600; }}
QLabel[variant="subtitle"]{{ font-size: 16px; font-weight: 600; }}
QLabel[variant="caption"] {{ font-size: 11px; color: {t['text_secondary']}; }}
QLabel[variant="muted"]   {{ color: {t['text_secondary']}; }}

/* ===================== Conteneurs ===================== */
QSplitter::handle {{ background-color: {t['border']}; }}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical {{ height: 2px; }}
QSplitter::handle:hover {{ background-color: {t['accent']}; }}
QScrollArea {{ border: none; background: transparent; }}

/* Cartes / panneaux : surface + bordure + coins arrondis */
QFrame[variant="card"] {{
    background-color: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: {('14')}px;
}}
QFrame[variant="surface"] {{
    background-color: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}

/* ===================== Champs de saisie ===================== */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit,
QTextEdit, QAbstractSpinBox {{
    background-color: {t['surface_alt']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 9px;
    selection-background-color: {t['accent']};
    selection-color: {t['on_accent']};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
QPlainTextEdit:hover, QTextEdit:hover, QAbstractSpinBox:hover {{
    border-color: {t['border_strong']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus, QAbstractSpinBox:focus {{
    border: 1px solid {t['accent']};
}}
QLineEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled {{
    color: {t['muted']}; background-color: {t['surface']};
}}
/* État d'erreur (propriété dynamique state="error") */
QLineEdit[state="error"], QComboBox[state="error"], QPlainTextEdit[state="error"] {{
    border: 1px solid {t['error']};
}}
QComboBox::drop-down {{ border: none; width: 22px; subcontrol-position: center right; }}
QComboBox QAbstractItemView {{
    background-color: {t['elevated']};
    color: {t['text']};
    border: 1px solid {t['border_strong']};
    border-radius: 8px;
    selection-background-color: {t['accent']};
    selection-color: {t['on_accent']};
    padding: 4px;
}}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    width: 18px; border: none; background: transparent;
}}

/* ===================== Boutons ===================== */
QPushButton {{
    background-color: {t['surface_alt']};
    color: {t['text']};
    border: 1px solid {t['border_strong']};
    border-radius: 8px;
    padding: 7px 15px;
    min-height: 16px;
}}
QPushButton:hover {{ background-color: {t['elevated']}; border-color: {t['accent']}; }}
QPushButton:pressed {{ background-color: {t['accent_active']}; color: {t['on_accent']}; }}
QPushButton:focus {{ border: 1px solid {t['accent']}; }}
QPushButton:checked {{
    background-color: {t['accent']}; color: {t['on_accent']}; border-color: {t['accent']};
}}
QPushButton:disabled {{ color: {t['muted']}; border-color: {t['border']}; background-color: {t['surface']}; }}

/* Variante primaire (accent="true" conservé pour compat + variant="primary") */
QPushButton[accent="true"], QPushButton[variant="primary"] {{
    background-color: {t['accent']}; color: {t['on_accent']};
    border: 1px solid {t['accent']}; font-weight: 600;
}}
QPushButton[accent="true"]:hover, QPushButton[variant="primary"]:hover {{
    background-color: {t['accent_hover']}; border-color: {t['accent_hover']};
}}
QPushButton[accent="true"]:pressed, QPushButton[variant="primary"]:pressed {{
    background-color: {t['accent_active']};
}}
/* Variante fantôme (ghost) */
QPushButton[variant="ghost"] {{
    background: transparent; border: 1px solid transparent; color: {t['text_secondary']};
}}
QPushButton[variant="ghost"]:hover {{ background-color: {t['surface_alt']}; color: {t['text']}; }}
/* Variante danger */
QPushButton[variant="danger"] {{
    background-color: {t['error']}; color: #FFFFFF; border: 1px solid {t['error']}; font-weight: 600;
}}
QPushButton[variant="danger"]:hover {{ background-color: #DC2626; border-color: #DC2626; }}

QToolButton {{
    background-color: transparent;
    color: {t['text']};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 9px;
}}
QToolButton:hover {{ background-color: {t['surface_alt']}; border-color: {t['border_strong']}; }}
QToolButton:pressed, QToolButton:checked {{
    background-color: {t['accent']}; color: {t['on_accent']};
}}
QToolButton:focus {{ border: 1px solid {t['accent']}; }}
QToolButton::menu-indicator {{ image: none; }}
/* QToolButton primaire (accent="true" / variant="primary") */
QToolButton[accent="true"], QToolButton[variant="primary"] {{
    background-color: {t['accent']}; color: {t['on_accent']};
    border: 1px solid {t['accent']}; font-weight: 600; padding: 8px 14px;
}}
QToolButton[accent="true"]:hover, QToolButton[variant="primary"]:hover {{
    background-color: {t['accent_hover']}; border-color: {t['accent_hover']};
}}
QToolButton[accent="true"]:pressed, QToolButton[variant="primary"]:pressed {{
    background-color: {t['accent_active']};
}}

/* ===================== Barre d'outils ===================== */
QToolBar {{
    background-color: {t['surface']};
    border: none;
    border-bottom: 1px solid {t['border']};
    padding: 6px 8px;
    spacing: 4px;
}}
QToolBar QToolButton {{ padding: 7px 11px; }}
QToolBar::separator {{ background-color: {t['border']}; width: 1px; margin: 6px 6px; }}

/* ===================== Onglets ===================== */
QTabWidget::pane {{
    border: 1px solid {t['border']}; border-radius: 10px; top: -1px;
    background-color: {t['surface']};
}}
QTabBar::tab {{
    background: transparent; color: {t['text_secondary']};
    padding: 8px 18px; margin-right: 2px; border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:hover {{ color: {t['text']}; }}
QTabBar::tab:selected {{ color: {t['accent']}; border-bottom: 2px solid {t['accent']}; font-weight: 600; }}

/* ===================== Listes & tableaux ===================== */
QListWidget, QTreeWidget, QTableWidget, QTableView, QTreeView {{
    background-color: {t['surface']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 4px;
    alternate-background-color: {t['surface_alt']};
}}
QListWidget::item, QTreeWidget::item {{ padding: 7px 9px; border-radius: 7px; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background-color: {t['surface_alt']}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {t['accent']}; color: {t['on_accent']};
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {t['selection']}; color: {t['text']};
}}
QHeaderView::section {{
    background-color: {t['surface_alt']}; color: {t['text_secondary']};
    border: none; border-bottom: 1px solid {t['border']};
    padding: 7px 9px; font-weight: 600;
}}

/* ===================== Cases, radios, interrupteurs ===================== */
QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px; height: 18px;
    border: 1px solid {t['border_strong']};
    border-radius: 5px; background-color: {t['surface_alt']};
}}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {t['accent']}; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {t['accent']}; border-color: {t['accent']};
}}

/* Curseurs (sliders) */
QSlider::groove:horizontal {{ height: 4px; background: {t['surface_alt']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    width: 16px; height: 16px; margin: -7px 0; border-radius: 8px;
    background: {t['accent']}; border: 2px solid {t['surface']};
}}
QSlider::handle:horizontal:hover {{ background: {t['accent_hover']}; }}

/* ===================== Barres de défilement ===================== */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['border_strong']}; border-radius: 5px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {t['accent']}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t['border_strong']}; border-radius: 5px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background: {t['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

/* ===================== Menus ===================== */
QMenuBar {{ background-color: {t['surface']}; border-bottom: 1px solid {t['border']}; }}
QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
QMenuBar::item:selected {{ background-color: {t['surface_alt']}; border-radius: 6px; }}
QMenu {{
    background-color: {t['elevated']}; border: 1px solid {t['border_strong']};
    border-radius: 10px; padding: 6px;
}}
QMenu::item {{ padding: 7px 22px 7px 14px; border-radius: 7px; }}
QMenu::item:selected {{ background-color: {t['accent']}; color: {t['on_accent']}; }}
QMenu::separator {{ height: 1px; background: {t['border']}; margin: 5px 8px; }}

/* ===================== Dock & barre d'état ===================== */
QDockWidget {{ titlebar-close-icon: none; }}
QDockWidget::title {{
    background-color: {t['surface']}; color: {t['text_secondary']};
    padding: 8px 11px; border-bottom: 1px solid {t['border']}; font-weight: 600;
}}
QStatusBar {{
    background-color: {t['surface']}; color: {t['text_secondary']};
    border-top: 1px solid {t['border']};
}}
QStatusBar::item {{ border: none; }}

/* ===================== Groupes & séparateurs ===================== */
QGroupBox {{
    border: 1px solid {t['border']}; border-radius: 10px;
    margin-top: 14px; padding: 12px;
    background-color: {t['surface']};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 12px; padding: 0 5px;
    color: {t['accent']}; font-weight: 600;
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {t['border']}; }}

/* ===================== Infobulles, progression, dialogues ===================== */
QToolTip {{
    background-color: {t['elevated']}; color: {t['text']};
    border: 1px solid {t['border_strong']}; border-radius: 8px; padding: 6px 9px;
}}
QProgressBar {{
    border: 1px solid {t['border']}; border-radius: 8px;
    background-color: {t['surface_alt']}; text-align: center; min-height: 8px;
}}
QProgressBar::chunk {{
    border-radius: 7px;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {t['accent']}, stop:1 {t['accent_2']});
}}

/* ===================== Sidebar (navigation) ===================== */
#sidebar {{ background-color: {t['surface']}; border-right: 1px solid {t['border']}; }}
#sidebar QListWidget {{ background: transparent; border: none; }}

/* ===================== Console de logs (monospace) ===================== */
#logConsole {{
    background-color: {t['surface_alt']};
    border: 1px solid {t['border']}; border-radius: 10px;
    font-family: {t['font_mono']}; font-size: 13px;
}}

/* ===================== Pastilles / badges sémantiques ===================== */
QLabel[badge="success"] {{ color: {t['success']}; font-weight: 600; }}
QLabel[badge="warning"] {{ color: {t['warning']}; font-weight: 600; }}
QLabel[badge="error"]   {{ color: {t['error']}; font-weight: 600; }}
QLabel[badge="info"]    {{ color: {t['info']}; font-weight: 600; }}
"""
