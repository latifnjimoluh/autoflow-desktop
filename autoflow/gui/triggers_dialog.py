"""Dialogue de configuration des **déclencheurs** d'un workflow (no-code).

Permet d'ajouter/retirer des déclencheurs (fenêtre, fichier, presse-papiers,
inactivité, webhook) et d'éditer leurs paramètres via des champs concrets, dans
l'esprit du panneau de paramètres des actions. Les déclencheurs sont manipulés
sous forme de **dictionnaires** (format stocké dans le workflow).
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core import triggers
from ..core.triggers.registry import create_trigger, get_trigger_class


class TriggersDialog(QDialog):
    """Édite la liste des déclencheurs d'un workflow."""

    def __init__(self, current: list[dict[str, Any]] | None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Déclencheurs événementiels")
        self.resize(560, 480)
        self._triggers: list[dict[str, Any]] = [dict(t) for t in (current or [])]

        root = QVBoxLayout(self)
        intro = QLabel("Un déclencheur démarre ce workflow lorsqu'un événement "
                       "se produit (en complément de la planification).")
        intro.setWordWrap(True)
        intro.setProperty("variant", "muted")
        root.addWidget(intro)

        add_row = QHBoxLayout()
        self._type_combo = QComboBox()
        for type_name, label in triggers.available_triggers():
            self._type_combo.addItem(label, type_name)
        add_btn = QPushButton("➕ Ajouter")
        add_btn.clicked.connect(self._add)
        add_row.addWidget(self._type_combo, 1)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._select)
        root.addWidget(self.list, 1)

        remove_btn = QPushButton("🗑 Retirer le déclencheur sélectionné")
        remove_btn.setProperty("variant", "ghost")
        remove_btn.clicked.connect(self._remove)
        root.addWidget(remove_btn)

        self._form_host = QWidget()
        self._form = QFormLayout(self._form_host)
        root.addWidget(self._form_host)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._editors: dict[str, Any] = {}
        self._refresh_list()

    # -- Liste -------------------------------------------------------------
    def _refresh_list(self) -> None:
        self.list.clear()
        for trig in self._triggers:
            try:
                summary = triggers.trigger_from_dict(trig).summary()
            except Exception:  # noqa: BLE001
                summary = trig.get("type", "?")
            self.list.addItem(summary)

    def _add(self) -> None:
        type_name = self._type_combo.currentData()
        self._triggers.append(create_trigger(type_name).to_dict())
        self._refresh_list()
        self.list.setCurrentRow(len(self._triggers) - 1)

    def _remove(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._triggers):
            del self._triggers[row]
            self._refresh_list()

    # -- Édition des paramètres -------------------------------------------
    def _select(self, row: int) -> None:
        self._clear_form()
        if not (0 <= row < len(self._triggers)):
            return
        trig = self._triggers[row]
        cls = get_trigger_class(trig["type"])
        self._editors = {}
        for spec in cls.param_specs():
            widget = self._make_editor(spec, trig["params"].get(spec.name, spec.default), row)
            self._editors[spec.name] = widget
            self._form.addRow(spec.label, widget)

    def _make_editor(self, spec: Any, value: Any, row: int) -> QWidget:
        if spec.type == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            w.toggled.connect(lambda v, n=spec.name: self._update(row, n, bool(v)))
            return w
        if spec.type == "int":
            w = QSpinBox()
            w.setRange(int(spec.min_value or 0), int(spec.max_value or 1_000_000))
            w.setValue(int(value or 0))
            w.valueChanged.connect(lambda v, n=spec.name: self._update(row, n, int(v)))
            return w
        if spec.type == "float":
            w = QDoubleSpinBox()
            w.setRange(float(spec.min_value or 0.0), float(spec.max_value or 1_000_000.0))
            w.setValue(float(value or 0.0))
            w.valueChanged.connect(lambda v, n=spec.name: self._update(row, n, float(v)))
            return w
        if spec.type == "choice":
            w = QComboBox()
            for choice in (spec.choices or []):
                w.addItem(str(choice), choice)
            idx = w.findData(value)
            if idx >= 0:
                w.setCurrentIndex(idx)
            w.currentIndexChanged.connect(
                lambda _i, n=spec.name, cb=w: self._update(row, n, cb.currentData()))
            return w
        w = QLineEdit(str(value or ""))
        if spec.placeholder:
            w.setPlaceholderText(spec.placeholder)
        w.textChanged.connect(lambda t, n=spec.name: self._update(row, n, t))
        return w

    def _update(self, row: int, name: str, value: Any) -> None:
        if 0 <= row < len(self._triggers):
            self._triggers[row]["params"][name] = value
            item = self.list.item(row)
            if item is not None:
                try:
                    item.setText(triggers.trigger_from_dict(self._triggers[row]).summary())
                except Exception:  # noqa: BLE001
                    pass

    def _clear_form(self) -> None:
        while self._form.count():
            item = self._form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def result_triggers(self) -> list[dict[str, Any]]:
        """Renvoie la liste des déclencheurs configurés."""
        return [dict(t) for t in self._triggers]
