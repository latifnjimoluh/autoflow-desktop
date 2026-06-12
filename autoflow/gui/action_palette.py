"""Palette d'actions « façon n8n » : catégorisée, cherchable, glissable.

Présente toutes les actions disponibles regroupées par catégorie, avec une barre
de recherche. L'utilisateur ajoute une action d'un clic (bouton « Ajouter ») ou
par double-clic. Réutilisable comme panneau latéral **ou** comme fenêtre
surgissante (pour le bouton « + » de la vue en nœuds).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core import registry
from .icons import action_icon


class ActionPalette(QWidget):
    """Liste cherchable des actions disponibles, groupée par catégorie."""

    action_chosen = Signal(str)  # type_name choisi

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔎 Rechercher une action…")
        self.search.textChanged.connect(self._refresh)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_double)
        layout.addWidget(self.list)

        self._entries = self._collect()
        self._refresh()

    def _collect(self) -> list[tuple[str, str, str]]:
        """Renvoie ``(type_name, label, category)`` pour toutes les actions."""
        entries = []
        for type_name, label in registry.available_types():
            cls = registry.get_action_class(type_name)
            entries.append((type_name, label, getattr(cls, "category", "Général")))
        entries.sort(key=lambda e: (e[2].lower(), e[1].lower()))
        return entries

    def _refresh(self) -> None:
        text = self.search.text().strip().lower()
        self.list.clear()
        current_cat = None
        for type_name, label, category in self._entries:
            if text and text not in f"{label} {category} {type_name}".lower():
                continue
            if category != current_cat:
                current_cat = category
                header = QListWidgetItem(f"— {category} —")
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list.addItem(header)
            item = QListWidgetItem(f"   {action_icon(type_name, category)}  {label}")
            item.setData(Qt.ItemDataRole.UserRole, type_name)
            self.list.addItem(item)

    def _on_double(self, item: QListWidgetItem) -> None:
        type_name = item.data(Qt.ItemDataRole.UserRole)
        if type_name:
            self.action_chosen.emit(str(type_name))

    def selected_type(self) -> str | None:
        item = self.list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)


class ActionPaletteDialog(QDialog):
    """Fenêtre surgissante de choix d'action (utilisée par le bouton « + »)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter une action")
        self.resize(360, 480)
        self.chosen_type: str | None = None
        layout = QVBoxLayout(self)
        self.palette = ActionPalette()
        self.palette.action_chosen.connect(self._choose)
        layout.addWidget(self.palette)

    def _choose(self, type_name: str) -> None:
        self.chosen_type = type_name
        self.accept()
