"""Dialogue de capture à l'écran : position, région ou couleur de pixel.

Affiche en **temps réel** la position du curseur (et la couleur sous le curseur
en mode pixel), puis capture la valeur sur clic. Pour une région, l'utilisateur
capture successivement le coin haut-gauche puis le coin bas-droit.

La capture interroge la façade d'entrées (:class:`InputBackend`) — donc aucune
dépendance directe à pyautogui ici. Sans façade (tests), le dialogue se construit
mais affiche « indisponible ».
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CaptureDialog(QDialog):
    """Capture interactive d'une position / région / pixel à l'écran."""

    def __init__(self, inputs: Any, mode: str = "position", parent=None) -> None:
        super().__init__(parent)
        self._inputs = inputs
        self._mode = mode  # "position" | "region" | "pixel"
        self.result_value: dict[str, int | str] = {}
        self._corner1: tuple[int, int] | None = None
        self._last = (0, 0)
        self._last_color = "#000000"

        titres = {
            "position": "Capturer une position",
            "region": "Capturer une région",
            "pixel": "Capturer un pixel",
        }
        self.setWindowTitle(titres.get(mode, "Capturer"))
        layout = QVBoxLayout(self)

        consignes = {
            "position": "Déplacez la souris à l'endroit voulu puis cliquez « Capturer ».",
            "region": "Capturez d'abord le coin haut-gauche, puis le coin bas-droit.",
            "pixel": "Pointez le pixel voulu puis cliquez « Capturer ».",
        }
        layout.addWidget(QLabel(consignes.get(mode, "")))

        self.live = QLabel("Position : —")
        layout.addWidget(self.live)
        self.swatch = QLabel("")
        if mode == "pixel":
            self.swatch.setMinimumHeight(24)
            layout.addWidget(self.swatch)

        self.capture_btn = QPushButton("📍 Capturer")
        self.capture_btn.clicked.connect(self._capture)
        layout.addWidget(self.capture_btn)

        self.status = QLabel("")
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _refresh(self) -> None:
        if self._inputs is None:
            self.live.setText("Position : indisponible (aucun écran).")
            return
        try:
            x, y = self._inputs.position()
            self._last = (int(x), int(y))
            text = f"Position : X={x}  Y={y}"
            if self._mode == "pixel":
                try:
                    r, g, b = self._inputs.pixel(int(x), int(y))
                    self._last_color = f"#{r:02x}{g:02x}{b:02x}"
                    text += f"   Couleur : {self._last_color}"
                    self.swatch.setStyleSheet(f"background-color: {self._last_color};")
                except Exception:  # noqa: BLE001
                    pass
            self.live.setText(text)
        except Exception:  # noqa: BLE001
            self.live.setText("Position : indisponible.")

    def _capture(self) -> None:
        x, y = self._last
        if self._mode == "position":
            self.result_value = {"x": x, "y": y}
            self._finish()
        elif self._mode == "pixel":
            self.result_value = {"x": x, "y": y, "color": self._last_color}
            self._finish()
        elif self._mode == "region":
            if self._corner1 is None:
                self._corner1 = (x, y)
                self.status.setText(f"Coin 1 : ({x}, {y}). Capturez le coin 2.")
            else:
                x1, y1 = self._corner1
                self.result_value = {
                    "x": min(x1, x), "y": min(y1, y),
                    "width": abs(x - x1), "height": abs(y - y1),
                }
                self._finish()

    def _finish(self) -> None:
        self._timer.stop()
        self.accept()
