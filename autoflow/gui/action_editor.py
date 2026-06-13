"""Panneau central : édition de la séquence d'actions d'un workflow."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..core import registry
from ..core.actions.base import Action


class ActionEditorPanel(QWidget):
    """Liste ordonnée des actions, avec ajout/édition/déplacement."""

    selected = Signal(int)
    add_requested = Signal(str)      # type_name de l'action à ajouter
    remove_requested = Signal()
    move_up_requested = Signal()
    move_down_requested = Signal()
    toggle_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Bouton « Ajouter une action » avec menu déroulant par catégorie.
        self._add_button = QToolButton()
        self._add_button.setText("Ajouter une action ▾")
        self._add_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._add_button.setMenu(self._build_add_menu())
        layout.addWidget(self._add_button)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self.selected.emit)
        self.list.itemDoubleClicked.connect(lambda _i: self.toggle_requested.emit())
        layout.addWidget(self.list)

        boutons = QHBoxLayout()
        self._btn_up = QPushButton("Monter")
        self._btn_down = QPushButton("Descendre")
        self._btn_toggle = QPushButton("Activer/Désactiver")
        self._btn_del = QPushButton("Supprimer")
        self._btn_up.clicked.connect(self.move_up_requested.emit)
        self._btn_down.clicked.connect(self.move_down_requested.emit)
        self._btn_toggle.clicked.connect(self.toggle_requested.emit)
        self._btn_del.clicked.connect(self.remove_requested.emit)
        for btn in (self._btn_up, self._btn_down, self._btn_toggle, self._btn_del):
            boutons.addWidget(btn)
        layout.addLayout(boutons)

    def _build_add_menu(self) -> QMenu:
        """Construit le menu d'ajout, regroupé par catégorie d'action."""
        menu = QMenu(self)
        categories: dict[str, list[tuple[str, str]]] = {}
        for type_name, label in registry.available_types():
            cls = registry.get_action_class(type_name)
            categories.setdefault(getattr(cls, "category", "Général"), []).append(
                (type_name, label))
        for category in sorted(categories):
            sous_menu = menu.addMenu(category)
            for type_name, label in sorted(categories[category], key=lambda t: t[1]):
                action = QAction(label, self)
                action.triggered.connect(
                    lambda _checked=False, t=type_name: self.add_requested.emit(t))
                sous_menu.addAction(action)
        return menu

    def set_actions(self, actions: list[Action], current: int = -1) -> None:
        """Affiche la séquence d'actions avec leur résumé et leur état."""
        self.list.blockSignals(True)
        self.list.clear()
        for action in actions:
            prefixe = "" if action.enabled else "✕ "
            item = QListWidgetItem(f"{prefixe}{action.summary()}")
            if not action.enabled:
                item.setForeground(item.foreground())  # gris géré par le style
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            self.list.addItem(item)
        if 0 <= current < len(actions):
            self.list.setCurrentRow(current)
        self.list.blockSignals(False)

    def current_row(self) -> int:
        """Renvoie l'indice de l'action sélectionnée (ou -1)."""
        return self.list.currentRow()
