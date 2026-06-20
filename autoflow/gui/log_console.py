"""Console de logs horodatée, monospace et colorée par niveau (thème-aware).

Le fond, la police et les couleurs par niveau proviennent des tokens de design
(via :func:`autoflow.gui.theme.palette`) : la console suit donc la bascule
clair/sombre. L'objet porte ``objectName = "logConsole"`` ciblé par le QSS.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit

from ..utils.logging_setup import format_log
from .theme import palette


def _level_colors(p: dict[str, str]) -> dict[str, str]:
    """Associe chaque niveau de log à une couleur sémantique du thème."""
    return {
        "info": p["text"],
        "action": p["accent_2"],
        "warning": p["warning"],
        "error": p["error"],
    }


class LogConsole(QPlainTextEdit):
    """Affiche les messages d'exécution, horodatés et colorés par niveau."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("logConsole")
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self._colors = _level_colors(palette())

    def refresh_theme(self) -> None:
        """Recalcule les couleurs de niveau après une bascule de thème."""
        self._colors = _level_colors(palette())

    def append_log(self, message: str, level: str = "info") -> None:
        """Ajoute une ligne horodatée à la console (slot thread-safe via signal)."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._colors.get(level, self._colors["info"])))
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(format_log(message, level) + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_logs(self) -> None:
        """Vide la console."""
        self.clear()
