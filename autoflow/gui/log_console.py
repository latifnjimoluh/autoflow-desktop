"""Console de logs horodatée."""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit

from ..utils.logging_setup import format_log

# Couleurs par niveau de message.
_COLORS = {
    "info": "#d4d4d4",
    "action": "#4ec9b0",
    "warning": "#dcdcaa",
    "error": "#f48771",
}


class LogConsole(QPlainTextEdit):
    """Affiche les messages d'exécution, horodatés et colorés par niveau."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setStyleSheet("background-color:#1e1e1e; font-family:Consolas, monospace;")

    def append_log(self, message: str, level: str = "info") -> None:
        """Ajoute une ligne horodatée à la console (slot thread-safe via signal)."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(_COLORS.get(level, "#d4d4d4")))
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(format_log(message, level) + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_logs(self) -> None:
        """Vide la console."""
        self.clear()
