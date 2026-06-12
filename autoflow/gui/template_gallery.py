"""Galerie de modèles : vue parcourable, catégorisée et cherchable.

Présente les modèles fournis avec AutoFlow sous forme de cartes (icône, titre,
description en langage simple), filtrables par texte et par catégorie. Le bouton
« Utiliser ce modèle » sélectionne le modèle ; l'appelant le clone alors dans
l'espace de l'utilisateur (prêt à éditer).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ..core import templates as templates_mod
from ..core.templates import Template


class TemplateGallery(QDialog):
    """Boîte de dialogue présentant la galerie de modèles."""

    def __init__(self, parent=None, directory=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Galerie de modèles — démarrez en un clic")
        self.resize(720, 520)
        self.selected_template: Template | None = None
        self._templates = templates_mod.load_templates(directory)

        layout = QVBoxLayout(self)
        intro = QLabel("Choisissez un modèle prêt à l'emploi : il sera copié dans "
                       "vos workflows, où vous pourrez l'adapter librement.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Barre de filtres : recherche + catégorie.
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔎 Rechercher un modèle…")
        self.search.textChanged.connect(self._refresh)
        self.category = QComboBox()
        self.category.addItem("Toutes les catégories", "")
        for cat in templates_mod.categories(directory):
            self.category.addItem(cat, cat)
        self.category.currentIndexChanged.connect(self._refresh)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.category)
        layout.addLayout(filters)

        # Corps : liste des modèles + détail.
        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._show_detail)
        self.list.itemDoubleClicked.connect(lambda _i: self._use())
        body.addWidget(self.list, 2)

        self.detail = QLabel("Sélectionnez un modèle pour voir sa description.")
        self.detail.setWordWrap(True)
        self.detail.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.detail.setStyleSheet("padding: 8px;")
        body.addWidget(self.detail, 1)
        layout.addLayout(body)

        buttons = QDialogButtonBox()
        self.use_btn = buttons.addButton("Utiliser ce modèle",
                                         QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.use_btn.clicked.connect(self._use)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh()

    def _refresh(self) -> None:
        """Reconstruit la liste selon les filtres recherche/catégorie."""
        text = self.search.text().strip().lower()
        category = self.category.currentData()
        self.list.clear()
        for tpl in self._templates:
            if category and tpl.category != category:
                continue
            haystack = f"{tpl.name} {tpl.description} {tpl.category}".lower()
            if text and text not in haystack:
                continue
            item = QListWidgetItem(f"{tpl.icon}  {tpl.name}")
            item.setData(Qt.ItemDataRole.UserRole, tpl)
            item.setToolTip(tpl.description)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.detail.setText("Aucun modèle ne correspond à votre recherche.")

    def _show_detail(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        tpl: Template = item.data(Qt.ItemDataRole.UserRole)
        nb = len(tpl.data.get("actions", []))
        self.detail.setText(
            f"<h3>{tpl.icon} {tpl.name}</h3>"
            f"<p><b>Catégorie :</b> {tpl.category}</p>"
            f"<p>{tpl.description}</p>"
            f"<p><i>{nb} action(s) préconfigurée(s).</i></p>"
        )

    def _use(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        self.selected_template = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
