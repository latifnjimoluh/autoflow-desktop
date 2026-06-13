"""Éditeur réutilisable d'une séquence d'actions (utilisé pour l'imbrication)."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..core import registry
from ..core.actions.base import Action
from .action_editor import ActionEditorPanel
from .param_panel import ParamPanel


class SequenceEditorWidget(QWidget):
    """Édite une liste d'actions en place (ajout, ordre, suppression, params).

    Si une action sélectionnée est un conteneur (condition, boucle), un bouton
    permet d'éditer récursivement ses sous-actions.
    """

    def __init__(self, actions: list[Action], parent=None) -> None:
        super().__init__(parent)
        self.actions = actions
        layout = QHBoxLayout(self)

        self.editor = ActionEditorPanel()
        self.param = ParamPanel()
        layout.addWidget(self.editor, 3)

        right = QWidget()
        from PySide6.QtWidgets import QVBoxLayout

        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.param)
        self.children_button = QPushButton("Modifier les sous-actions…")
        self.children_button.setVisible(False)
        self.children_button.clicked.connect(self._edit_children)
        right_layout.addWidget(self.children_button)
        layout.addWidget(right, 2)

        self.editor.add_requested.connect(self._add)
        self.editor.remove_requested.connect(self._remove)
        self.editor.move_up_requested.connect(lambda: self._move(-1))
        self.editor.move_down_requested.connect(lambda: self._move(1))
        self.editor.toggle_requested.connect(self._toggle)
        self.editor.selected.connect(self._select)

        self.refresh()

    def refresh(self, select: int = -1) -> None:
        self.editor.set_actions(self.actions, select)
        self._select(select)

    def _select(self, index: int) -> None:
        if 0 <= index < len(self.actions):
            action = self.actions[index]
            self.param.set_action(action, lambda: self.editor.set_actions(self.actions, index))
            self.children_button.setVisible(bool(action.child_groups()))
        else:
            self.param.set_action(None)
            self.children_button.setVisible(False)

    def _add(self, type_name: str) -> None:
        self.actions.append(registry.create_action(type_name))
        self.refresh(select=len(self.actions) - 1)

    def _remove(self) -> None:
        row = self.editor.current_row()
        if 0 <= row < len(self.actions):
            del self.actions[row]
            self.refresh(select=min(row, len(self.actions) - 1))

    def _move(self, delta: int) -> None:
        row = self.editor.current_row()
        new = row + delta
        if 0 <= row < len(self.actions) and 0 <= new < len(self.actions):
            self.actions[row], self.actions[new] = self.actions[new], self.actions[row]
            self.refresh(select=new)

    def _toggle(self) -> None:
        row = self.editor.current_row()
        if 0 <= row < len(self.actions):
            self.actions[row].enabled = not self.actions[row].enabled
            self.refresh(select=row)

    def _edit_children(self) -> None:
        from .child_editor import ChildEditorDialog

        row = self.editor.current_row()
        if 0 <= row < len(self.actions):
            dialog = ChildEditorDialog(self.actions[row], self)
            dialog.exec()
            self.refresh(select=row)
