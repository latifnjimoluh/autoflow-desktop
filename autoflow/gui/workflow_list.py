"""Panneau gauche : liste des workflows et actions associées."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WorkflowListPanel(QWidget):
    """Affiche la liste des workflows et expose les actions de gestion."""

    selected = Signal(int)
    new_requested = Signal()
    duplicate_requested = Signal()
    delete_requested = Signal()
    import_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self.selected.emit)
        layout.addWidget(self.list)

        ligne1 = QHBoxLayout()
        self._btn_new = QPushButton("Nouveau")
        self._btn_dup = QPushButton("Dupliquer")
        self._btn_del = QPushButton("Supprimer")
        self._btn_new.clicked.connect(self.new_requested.emit)
        self._btn_dup.clicked.connect(self.duplicate_requested.emit)
        self._btn_del.clicked.connect(self.delete_requested.emit)
        for btn in (self._btn_new, self._btn_dup, self._btn_del):
            ligne1.addWidget(btn)
        layout.addLayout(ligne1)

        ligne2 = QHBoxLayout()
        self._btn_imp = QPushButton("Importer")
        self._btn_exp = QPushButton("Exporter")
        self._btn_imp.clicked.connect(self.import_requested.emit)
        self._btn_exp.clicked.connect(self.export_requested.emit)
        ligne2.addWidget(self._btn_imp)
        ligne2.addWidget(self._btn_exp)
        layout.addLayout(ligne2)

    def set_workflows(self, names: list[str], current: int = 0) -> None:
        """Remplit la liste avec les noms de workflows."""
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItems(names)
        if 0 <= current < len(names):
            self.list.setCurrentRow(current)
        self.list.blockSignals(False)

    def current_row(self) -> int:
        """Renvoie l'indice du workflow sélectionné (ou -1)."""
        return self.list.currentRow()
