"""Fenêtre « À propos » d'AutoFlow : identité, version, lien dépôt.

Soignée et cohérente avec le système de design : logo peint, titre, version,
courte description et lien vers le dépôt. Tout provient des tokens/branding.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..ui.branding import APP_NAME, APP_TAGLINE, REPO_URL, VERSION, app_icon
from .theme import palette


class AboutDialog(QDialog):
    """Boîte de dialogue « À propos » présentant l'application."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"À propos d'{APP_NAME}")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(16)
        icon = app_icon(96)
        logo = QLabel()
        if icon is not None:
            logo.setPixmap(icon.pixmap(72, 72))
        header.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        name = QLabel(APP_NAME)
        name.setProperty("variant", "title")
        tagline = QLabel(APP_TAGLINE)
        tagline.setProperty("variant", "muted")
        version = QLabel(f"Version {VERSION}")
        version.setProperty("variant", "caption")
        title_box.addWidget(name)
        title_box.addWidget(tagline)
        title_box.addWidget(version)
        header.addLayout(title_box, 1)
        root.addLayout(header)

        desc = QLabel(
            "AutoFlow assemble visuellement des workflows d'automatisation "
            "(clics, frappes, fenêtres, conditions, boucles) et les planifie — "
            "sans écrire de code.")
        desc.setWordWrap(True)
        desc.setProperty("variant", "muted")
        root.addWidget(desc)

        accent = palette()["accent"]
        link = QLabel(f'<a href="{REPO_URL}" style="color:{accent};">{REPO_URL}</a>')
        link.setOpenExternalLinks(True)
        link.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(link)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("Fermer")
        close.setProperty("variant", "primary")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)
