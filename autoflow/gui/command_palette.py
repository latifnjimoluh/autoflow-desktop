"""Palette de commandes (Ctrl+K) : lancer rapidement un workflow ou une action.

Liste cherchable de **commandes** (workflows à exécuter, actions à insérer,
commandes d'application). Filtrage instantané au clavier ; Entrée exécute la
commande sélectionnée. Construit et testable en mode offscreen.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


@dataclass
class Command:
    """Entrée de la palette : libellé affiché + action à exécuter."""

    label: str
    callback: Callable[[], None]
    category: str = ""

    def display(self) -> str:
        return f"{self.category} · {self.label}" if self.category else self.label


class CommandPalette(QDialog):
    """Boîte de recherche surgissante listant des commandes filtrables."""

    def __init__(self, commands: list[Command], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Palette de commandes")
        self.setMinimumWidth(520)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._commands = list(commands)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tapez pour rechercher une commande…")
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._run_current)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.itemActivated.connect(lambda _i: self._run_current())
        layout.addWidget(self.list)

        self._populate(self._commands)
        self.search.setFocus()

    def _populate(self, commands: list[Command]) -> None:
        self.list.clear()
        for cmd in commands:
            item = QListWidgetItem(cmd.display())
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        text = text.strip().lower()
        if not text:
            self._populate(self._commands)
            return
        matches = [c for c in self._commands if text in c.display().lower()]
        self._populate(matches)

    def _run_current(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        cmd: Command = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        cmd.callback()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Flèches : naviguer dans la liste même depuis le champ de recherche."""
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            row = self.list.currentRow()
            row += 1 if event.key() == Qt.Key.Key_Down else -1
            self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
            return
        super().keyPressEvent(event)


def build_default_commands(workflows: list[Any], run_workflow: Callable[[str], None],
                           extra: list[Command] | None = None) -> list[Command]:
    """Construit la liste de commandes par défaut (un lancement par workflow)."""
    commands: list[Command] = []
    for wf in workflows:
        name = getattr(wf, "name", str(wf))
        commands.append(Command(
            label=f"Exécuter « {name} »",
            callback=lambda n=name: run_workflow(n),
            category="Workflow"))
    if extra:
        commands.extend(extra)
    return commands
