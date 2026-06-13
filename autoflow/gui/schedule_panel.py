"""Panneau de configuration du planning d'un workflow."""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from ..models.workflow import SCHEDULE_MODES, Schedule

# Libellés français des modes de planning.
_MODE_LABELS = {
    "run_once": "Une seule fois",
    "loop_interval": "Boucle (intervalle)",
    "repeat_n": "Répéter N fois",
    "at_time": "À une heure précise",
    "hotkey_trigger": "Déclenché par raccourci",
}


class SchedulePanel(QWidget):
    """Édite le :class:`Schedule` du workflow courant."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._schedule: Schedule | None = None
        self._on_change: Callable[[], None] = lambda: None
        layout = QFormLayout(self)

        self.mode = QComboBox()
        for mode in SCHEDULE_MODES:
            self.mode.addItem(_MODE_LABELS.get(mode, mode), mode)
        self.mode.currentIndexChanged.connect(self._apply)
        layout.addRow("Mode", self.mode)

        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.0, 86400.0)
        self.interval.setDecimals(0)
        self.interval.setSuffix(" s")
        self.interval.valueChanged.connect(self._apply)
        layout.addRow("Intervalle", self.interval)

        self.max_iter = QSpinBox()
        self.max_iter.setRange(0, 1_000_000)
        self.max_iter.setToolTip("0 = infini")
        self.max_iter.valueChanged.connect(self._apply)
        layout.addRow("Itérations max (0 = ∞)", self.max_iter)

        self.at_time = QLineEdit()
        self.at_time.setPlaceholderText("HH:MM")
        self.at_time.textChanged.connect(self._apply)
        layout.addRow("Heure (HH:MM)", self.at_time)

        self.hotkey = QLineEdit()
        self.hotkey.setPlaceholderText("ex. ctrl+shift+r")
        self.hotkey.textChanged.connect(self._apply)
        layout.addRow("Raccourci déclencheur", self.hotkey)

        self._loading = False

    def set_schedule(self, schedule: Schedule | None,
                     on_change: Callable[[], None] | None = None) -> None:
        """Charge un planning dans le panneau."""
        self._on_change = on_change or (lambda: None)
        self._schedule = schedule
        self._loading = True
        if schedule is not None:
            index = self.mode.findData(schedule.mode)
            self.mode.setCurrentIndex(max(0, index))
            self.interval.setValue(float(schedule.interval_seconds))
            self.max_iter.setValue(int(schedule.max_iterations))
            self.at_time.setText(schedule.at_time)
            self.hotkey.setText(schedule.hotkey)
        self.setEnabled(schedule is not None)
        self._loading = False

    def _apply(self) -> None:
        """Répercute les valeurs des widgets dans le planning."""
        if self._schedule is None or self._loading:
            return
        self._schedule.mode = self.mode.currentData()
        self._schedule.interval_seconds = float(self.interval.value())
        self._schedule.max_iterations = int(self.max_iter.value())
        self._schedule.at_time = self.at_time.text().strip() or "08:00"
        self._schedule.hotkey = self.hotkey.text().strip() or "ctrl+shift+r"
        self._on_change()
