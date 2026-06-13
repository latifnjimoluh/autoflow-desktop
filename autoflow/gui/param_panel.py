"""Panneau de paramètres : formulaire dynamique généré depuis le schéma.

À partir de la liste des :class:`ParamSpec` d'une action, ce panneau construit
automatiquement les widgets adaptés et répercute les modifications dans l'action.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ..core.actions.base import Action, ParamSpec


class ParamPanel(QWidget):
    """Formulaire d'édition des paramètres de l'action sélectionnée."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = QFormLayout(self)
        self._action: Action | None = None
        self._on_change: Callable[[], None] = lambda: None
        self._placeholder = QLabel("Sélectionnez une action pour l'éditer.")
        self._layout.addRow(self._placeholder)

    # -- Construction du formulaire ---------------------------------------
    def set_action(self, action: Action | None,
                   on_change: Callable[[], None] | None = None) -> None:
        """Construit le formulaire pour ``action`` (ou le vide si ``None``)."""
        self._clear()
        self._action = action
        self._on_change = on_change or (lambda: None)
        if action is None:
            self._layout.addRow(QLabel("Aucune action sélectionnée."))
            return

        # Champs communs : activé + délai après.
        chk = QCheckBox()
        chk.setChecked(action.enabled)
        chk.toggled.connect(self._set_enabled)
        self._layout.addRow("Activée", chk)

        delay = QDoubleSpinBox()
        delay.setRange(0.0, 86400.0)
        delay.setDecimals(2)
        delay.setSingleStep(0.1)
        delay.setValue(float(action.delay_after))
        delay.valueChanged.connect(self._set_delay)
        self._layout.addRow("Délai après (s)", delay)

        for spec in action.param_specs():
            widget = self._build_widget(spec)
            if widget is not None:
                self._layout.addRow(spec.label, widget)

    def _build_widget(self, spec: ParamSpec) -> QWidget | None:
        """Crée le widget correspondant au type du paramètre."""
        value = self._action.params.get(spec.name, spec.default)

        if spec.type == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.toggled.connect(lambda v, n=spec.name: self._update(n, bool(v)))
            return widget

        if spec.type == "int":
            widget = QSpinBox()
            widget.setRange(-1_000_000, 1_000_000)
            widget.setValue(int(value or 0))
            widget.valueChanged.connect(lambda v, n=spec.name: self._update(n, int(v)))
            return widget

        if spec.type == "float":
            widget = QDoubleSpinBox()
            widget.setRange(-1_000_000.0, 1_000_000.0)
            widget.setDecimals(3)
            widget.setSingleStep(0.1)
            widget.setValue(float(value or 0.0))
            widget.valueChanged.connect(lambda v, n=spec.name: self._update(n, float(v)))
            return widget

        if spec.type == "choice":
            widget = QComboBox()
            widget.addItems([str(c) for c in (spec.choices or [])])
            if value is not None and str(value) in [str(c) for c in (spec.choices or [])]:
                widget.setCurrentText(str(value))
            widget.currentTextChanged.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if spec.type == "text":
            widget = QPlainTextEdit()
            widget.setPlainText(str(value or ""))
            widget.setMaximumHeight(80)
            widget.textChanged.connect(
                lambda w=widget, n=spec.name: self._update(n, w.toPlainText()))
            return widget

        if spec.type == "keys":
            widget = QLineEdit()
            widget.setText(_keys_to_text(value))
            widget.setPlaceholderText("ex. ctrl+end")
            widget.textChanged.connect(
                lambda v, n=spec.name: self._update(n, _text_to_keys(v)))
            return widget

        if spec.type == "file":
            return self._build_file_widget(spec, value)

        # Type ``str`` par défaut.
        widget = QLineEdit()
        widget.setText(str(value or ""))
        if spec.help:
            widget.setToolTip(spec.help)
        widget.textChanged.connect(lambda v, n=spec.name: self._update(n, v))
        return widget

    def _build_file_widget(self, spec: ParamSpec, value: Any) -> QWidget:
        """Crée un champ texte doublé d'un bouton « Parcourir »."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        line = QLineEdit()
        line.setText(str(value or ""))
        line.textChanged.connect(lambda v, n=spec.name: self._update(n, v))
        button = QPushButton("Parcourir…")

        def browse() -> None:
            path, _ = QFileDialog.getOpenFileName(self, spec.label)
            if path:
                line.setText(path)

        button.clicked.connect(browse)
        layout.addWidget(line)
        layout.addWidget(button)
        return container

    # -- Mises à jour ------------------------------------------------------
    def _update(self, name: str, value: Any) -> None:
        if self._action is not None:
            self._action.params[name] = value
            self._on_change()

    def _set_enabled(self, value: bool) -> None:
        if self._action is not None:
            self._action.enabled = bool(value)
            self._on_change()

    def _set_delay(self, value: float) -> None:
        if self._action is not None:
            self._action.delay_after = float(value)
            self._on_change()

    def _clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


def _keys_to_text(value: Any) -> str:
    """Convertit une liste de touches en texte « ctrl+end »."""
    if isinstance(value, list):
        return "+".join(str(k) for k in value)
    return str(value or "")


def _text_to_keys(text: str) -> list[str]:
    """Convertit « ctrl+end » en liste de touches."""
    return [k.strip().lower() for k in text.replace(",", "+").split("+") if k.strip()]
