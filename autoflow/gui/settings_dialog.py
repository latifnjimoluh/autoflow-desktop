"""Boîte de dialogue des réglages applicatifs."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ..settings import Settings


class SettingsDialog(QDialog):
    """Édite les réglages : failsafe, pause, Tesseract, thème, langue, etc."""

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Réglages — AutoFlow")
        self.settings = settings
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.failsafe = QCheckBox()
        self.failsafe.setChecked(settings.failsafe)
        form.addRow("Failsafe (souris coin haut-gauche)", self.failsafe)

        self.pause = QDoubleSpinBox()
        self.pause.setRange(0.0, 5.0)
        self.pause.setSingleStep(0.05)
        self.pause.setValue(settings.pyautogui_pause)
        form.addRow("Pause pyautogui (s)", self.pause)

        self.hotkey = QLineEdit(settings.emergency_hotkey)
        form.addRow("Raccourci d'arrêt d'urgence", self.hotkey)

        tess_row = QHBoxLayout()
        self.tesseract = QLineEdit(settings.tesseract_path)
        browse = QPushButton("Parcourir…")
        browse.clicked.connect(self._browse_tesseract)
        tess_row.addWidget(self.tesseract)
        tess_row.addWidget(browse)
        form.addRow("Chemin de Tesseract (OCR)", tess_row)

        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.theme)
        form.addRow("Thème", self.theme)

        self.language = QComboBox()
        self.language.addItems(["fr", "en"])
        self.language.setCurrentText(settings.language)
        form.addRow("Langue", self.language)

        self.notifications = QCheckBox()
        self.notifications.setChecked(settings.notifications)
        form.addRow("Notifications de bureau", self.notifications)

        self.autostart = QCheckBox()
        self.autostart.setChecked(settings.autostart)
        form.addRow("Démarrage automatique avec Windows", self.autostart)

        self.minimize = QCheckBox()
        self.minimize.setChecked(settings.minimize_to_tray)
        form.addRow("Réduire dans la barre des tâches", self.minimize)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_tesseract(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Exécutable Tesseract")
        if path:
            self.tesseract.setText(path)

    def result_settings(self) -> Settings:
        """Renvoie les réglages mis à jour d'après les champs."""
        self.settings.failsafe = self.failsafe.isChecked()
        self.settings.pyautogui_pause = float(self.pause.value())
        self.settings.emergency_hotkey = self.hotkey.text().strip() or "ctrl+shift+q"
        self.settings.tesseract_path = self.tesseract.text().strip()
        self.settings.theme = self.theme.currentText()
        self.settings.language = self.language.currentText()
        self.settings.notifications = self.notifications.isChecked()
        self.settings.autostart = self.autostart.isChecked()
        self.settings.minimize_to_tray = self.minimize.isChecked()
        return self.settings
