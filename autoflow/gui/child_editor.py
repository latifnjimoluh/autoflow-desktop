"""Dialogue d'édition des sous-actions d'une action de contrôle de flux."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTabWidget, QVBoxLayout

from ..core.actions.base import Action


class ChildEditorDialog(QDialog):
    """Édite récursivement les groupes d'enfants (alors/sinon, corps…)."""

    def __init__(self, action: Action, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Sous-actions — {action.summary()}")
        self.resize(820, 520)
        layout = QVBoxLayout(self)

        # Import différé pour éviter une dépendance circulaire à l'import.
        from .sequence_editor import SequenceEditorWidget

        tabs = QTabWidget()
        for nom, enfants in action.child_groups().items():
            tabs.addTab(SequenceEditorWidget(enfants), nom.capitalize())
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
