"""Façade presse-papiers s'appuyant sur Qt si disponible, sinon en mémoire.

Permet aux actions presse-papiers de fonctionner en mode réel (via ``QClipboard``)
comme en mode test/headless (repli interne), sans dépendance supplémentaire.
"""

from __future__ import annotations


class ClipboardBackend:
    """Lecture/écriture du presse-papiers, avec repli interne."""

    def __init__(self) -> None:
        self._fallback = ""

    def _qt_clipboard(self):
        """Renvoie le presse-papiers Qt si une application existe, sinon None."""
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            return app.clipboard() if app is not None else None
        except Exception:  # noqa: BLE001
            return None

    def set_text(self, text: str) -> None:
        """Écrit ``text`` dans le presse-papiers."""
        clip = self._qt_clipboard()
        if clip is not None:
            clip.setText(str(text))
        self._fallback = str(text)

    def get_text(self) -> str:
        """Renvoie le contenu texte du presse-papiers."""
        clip = self._qt_clipboard()
        if clip is not None:
            return clip.text()
        return self._fallback
