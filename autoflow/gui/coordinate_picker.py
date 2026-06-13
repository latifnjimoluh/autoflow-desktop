"""Sélecteur de coordonnées : affiche la position du curseur en temps réel."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class CoordinatePicker(QWidget):
    """Affiche la position courante de la souris et permet de la capturer.

    Émet :data:`captured` avec ``(x, y)`` lorsqu'on clique sur « Capturer ».
    L'affichage est rafraîchi par un timer qui interroge la façade d'entrées.
    """

    captured = Signal(int, int)

    def __init__(self, inputs, parent=None) -> None:
        super().__init__(parent)
        self._inputs = inputs
        layout = QHBoxLayout(self)

        self.label = QLabel("X: —  Y: —")
        self.button = QPushButton("Capturer la position")
        self.button.clicked.connect(self._capture)
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self._last = (0, 0)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._refresh)

    def start(self) -> None:
        """Démarre le rafraîchissement en temps réel."""
        self._timer.start()

    def stop(self) -> None:
        """Arrête le rafraîchissement."""
        self._timer.stop()

    def _refresh(self) -> None:
        """Interroge la position du curseur (sans planter si indisponible)."""
        try:
            x, y = self._inputs.position()
            self._last = (int(x), int(y))
            self.label.setText(f"X: {x}  Y: {y}")
        except Exception:  # noqa: BLE001 - pas d'affichage / pyautogui absent
            self.label.setText("Position indisponible")

    def _capture(self) -> None:
        """Émet la dernière position connue."""
        self.captured.emit(*self._last)
