"""Widgets « concrets » : remplacent les champs texte nus par des composants guidés.

Chaque widget capture/choisit une donnée plutôt que de la faire deviner :

- :class:`KeyCaptureField` : capture d'une touche réelle + liste cherchable ;
- :class:`HotkeyCaptureField` : capture d'une combinaison + constructeur manuel ;
- :class:`WindowSelectField` : liste des fenêtres ouvertes + titre manuel ;
- :class:`AppSelectField` : applications installées / parcourir / manuel ;
- :class:`ColorField` : sélecteur de couleur visuel ;
- :class:`ComboField` : liste éditable (variables, workflows…) ;
- :class:`PathField` : fichier ou dossier via sélecteur natif.

Tous émettent :data:`changed` avec la valeur normalisée. La capture en direct
(``pynput``) est importée **paresseusement** et dégrade proprement si absente, de
sorte que les widgets se construisent sans écran ni clavier (smoke tests).
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QCompleter,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..services.keys import (
    ALL_KEYS,
    MODIFIER_LABELS,
    MODIFIERS,
    keys_to_label,
    normalize_key,
)


class _CaptureMixin:
    """Outils communs de capture clavier via ``pynput`` (chargé paresseusement)."""

    def _start_listener(self, on_press: Callable[[Any], bool]) -> Any:
        try:
            from pynput import keyboard  # import paresseux volontaire
        except Exception:  # noqa: BLE001 - pynput absent / pas d'affichage
            return None
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        return listener


class KeyCaptureField(QWidget):
    """Choix d'une **touche unique** : capture en direct + liste cherchable."""

    changed = Signal(str)
    _captured = Signal(str)

    def __init__(self, value: str = "", placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for backend, label in ALL_KEYS:
            self.combo.addItem(f"{label}  ({backend})", backend)
        self.combo.setCompleter(self._completer())
        if placeholder:
            self.combo.lineEdit().setPlaceholderText(placeholder)
        self._set_value(value)
        self.combo.currentIndexChanged.connect(self._on_index)
        self.combo.lineEdit().editingFinished.connect(self._on_edit)

        self.btn = QPushButton("⌨ Capturer")
        self.btn.setToolTip("Cliquez puis appuyez sur la touche de votre choix.")
        self.btn.clicked.connect(self._capture)

        layout.addWidget(self.combo, 1)
        layout.addWidget(self.btn)
        self._listener = None
        self._captured.connect(self._apply_capture)

    def _completer(self) -> QCompleter:
        completer = QCompleter([f"{label}  ({backend})" for backend, label in ALL_KEYS])
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        return completer

    def _set_value(self, value: str) -> None:
        value = normalize_key(value)
        index = self.combo.findData(value)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        else:
            self.combo.setEditText(value)

    def value(self) -> str:
        data = self.combo.currentData()
        if data:
            return str(data)
        return normalize_key(self.combo.currentText().split("(")[0])

    def _on_index(self, _i: int) -> None:
        self.changed.emit(self.value())

    def _on_edit(self) -> None:
        self.changed.emit(self.value())

    def _capture(self) -> None:
        self.btn.setText("… appuyez sur une touche")
        self.btn.setEnabled(False)

        def on_press(key: Any) -> bool:
            from ..services.keys import pynput_to_name

            self._captured.emit(pynput_to_name(key))
            return False  # stoppe l'écoute après la première touche

        self._listener = _CaptureMixin()._start_listener(on_press)
        if self._listener is None:
            self.btn.setText("⌨ Capturer")
            self.btn.setEnabled(True)

    def _apply_capture(self, key_name: str) -> None:
        self._set_value(key_name)
        self.btn.setText("⌨ Capturer")
        self.btn.setEnabled(True)
        self.changed.emit(self.value())


class HotkeyCaptureField(QWidget):
    """Choix d'une **combinaison** : capture en direct + interrupteurs + touche."""

    changed = Signal(list)
    _captured = Signal(list)

    def __init__(self, value: Any = None, placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Ligne 1 : modificateurs + touche finale.
        builder = QHBoxLayout()
        self._mod_buttons: dict[str, QPushButton] = {}
        for mod in MODIFIERS:
            btn = QPushButton(MODIFIER_LABELS[mod])
            btn.setCheckable(True)
            btn.setMaximumWidth(60)
            btn.toggled.connect(self._emit)
            self._mod_buttons[mod] = btn
            builder.addWidget(btn)
        self.key_combo = QComboBox()
        self.key_combo.setEditable(True)
        for backend, label in ALL_KEYS:
            self.key_combo.addItem(label, backend)
        self.key_combo.currentIndexChanged.connect(self._emit)
        self.key_combo.lineEdit().editingFinished.connect(self._emit)
        builder.addWidget(self.key_combo, 1)
        layout.addLayout(builder)

        # Ligne 2 : bouton de capture + rendu visuel de la combinaison.
        bottom = QHBoxLayout()
        self.btn = QPushButton("⌨ Enregistrer le raccourci")
        self.btn.clicked.connect(self._capture)
        self.badge = QLabel("—")
        self.badge.setStyleSheet("font-weight: bold;")
        bottom.addWidget(self.btn)
        bottom.addWidget(self.badge, 1)
        layout.addLayout(bottom)

        self._set_value(value or [])
        self._listener = None
        self._captured.connect(self._apply_capture)

    def _set_value(self, keys: Any) -> None:
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.replace(",", "+").split("+") if k.strip()]
        keys = [normalize_key(k) for k in (keys or [])]
        for mod, btn in self._mod_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(mod in keys)
            btn.blockSignals(False)
        finals = [k for k in keys if k not in MODIFIERS]
        self.key_combo.blockSignals(True)
        if finals:
            idx = self.key_combo.findData(finals[-1])
            if idx >= 0:
                self.key_combo.setCurrentIndex(idx)
            else:
                self.key_combo.setEditText(finals[-1])
        self.key_combo.blockSignals(False)
        self._refresh_badge()

    def value(self) -> list[str]:
        mods = [m for m in MODIFIERS if self._mod_buttons[m].isChecked()]
        final = self.key_combo.currentData() or normalize_key(self.key_combo.currentText())
        keys = list(mods)
        if final and final not in keys:
            keys.append(str(final))
        return keys

    def _emit(self, *_a: Any) -> None:
        self._refresh_badge()
        self.changed.emit(self.value())

    def _refresh_badge(self) -> None:
        self.badge.setText(keys_to_label(self.value()) or "—")

    def _capture(self) -> None:
        self.btn.setText("… pressez la combinaison")
        self.btn.setEnabled(False)
        pressed: list[str] = []

        def on_press(key: Any) -> bool:
            from ..services.keys import is_modifier, pynput_to_name

            name = pynput_to_name(key)
            if name not in pressed:
                pressed.append(name)
            if not is_modifier(name):
                self._captured.emit(list(pressed))
                return False  # touche finale atteinte
            return True

        self._listener = _CaptureMixin()._start_listener(on_press)
        if self._listener is None:
            self.btn.setText("⌨ Enregistrer le raccourci")
            self.btn.setEnabled(True)

    def _apply_capture(self, keys: list[str]) -> None:
        self._set_value(keys)
        self.btn.setText("⌨ Enregistrer le raccourci")
        self.btn.setEnabled(True)
        self.changed.emit(self.value())


class WindowSelectField(QWidget):
    """Sélection d'une fenêtre **ouverte** + saisie manuelle d'un titre."""

    changed = Signal(str)

    def __init__(self, value: str = "", placeholder: str = "",
                 provider: Callable[[], list[str]] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._provider = provider or (lambda: [])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setEditable(True)
        if placeholder:
            self.combo.lineEdit().setPlaceholderText(placeholder)
        self.combo.setEditText(str(value or ""))
        self.combo.currentTextChanged.connect(self.changed.emit)
        self.btn = QPushButton("⟳")
        self.btn.setToolTip("Rafraîchir la liste des fenêtres ouvertes")
        self.btn.setMaximumWidth(36)
        self.btn.clicked.connect(self.refresh)
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.btn)
        self.refresh(keep=str(value or ""))

    def refresh(self, *_a: Any, keep: str | None = None) -> None:
        current = keep if keep is not None else self.combo.currentText()
        self.combo.blockSignals(True)
        self.combo.clear()
        try:
            titles = list(self._provider())
        except Exception:  # noqa: BLE001
            titles = []
        self.combo.addItems(titles)
        self.combo.setEditText(current)
        self.combo.blockSignals(False)

    def value(self) -> str:
        return self.combo.currentText()


class AppSelectField(QWidget):
    """Sélection d'une application : installées / parcourir / saisie manuelle."""

    changed = Signal(str)

    def __init__(self, value: str = "", placeholder: str = "",
                 provider: Callable[[], list[tuple[str, str]]] | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._provider = provider or (lambda: [])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setEditable(True)
        if placeholder:
            self.combo.lineEdit().setPlaceholderText(placeholder)
        try:
            for name, path in self._provider():
                self.combo.addItem(name, path)
        except Exception:  # noqa: BLE001
            pass
        self.combo.setEditText(str(value or ""))
        self.combo.currentIndexChanged.connect(self._on_index)
        self.combo.lineEdit().textChanged.connect(self.changed.emit)
        self.btn = QPushButton("Parcourir…")
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.btn)

    def _on_index(self, _i: int) -> None:
        path = self.combo.currentData()
        if path:
            self.combo.setEditText(str(path))

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une application ou un fichier")
        if path:
            self.combo.setEditText(path)

    def value(self) -> str:
        return self.combo.currentText()


class ColorField(QWidget):
    """Sélecteur de couleur visuel : pastille + valeur hexadécimale."""

    changed = Signal(str)

    def __init__(self, value: str = "#000000", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit(str(value or "#000000"))
        self.edit.setPlaceholderText("Ex : #3366ff")
        self.edit.textChanged.connect(self._on_text)
        self.swatch = QPushButton("Choisir…")
        self.swatch.clicked.connect(self._pick)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.swatch)
        self._refresh_swatch()

    def _on_text(self, text: str) -> None:
        self._refresh_swatch()
        self.changed.emit(text)

    def _pick(self) -> None:
        initial = QColor(self.edit.text() or "#000000")
        color = QColorDialog.getColor(initial, self, "Choisir une couleur")
        if color.isValid():
            self.edit.setText(color.name())

    def _refresh_swatch(self) -> None:
        color = QColor(self.edit.text() or "#000000")
        if color.isValid():
            self.swatch.setStyleSheet(
                f"background-color: {color.name()}; color: "
                f"{'#000' if color.lightness() > 128 else '#fff'};")

    def value(self) -> str:
        return self.edit.text()


class ComboField(QWidget):
    """Liste **éditable** alimentée par un fournisseur (variables, workflows…)."""

    changed = Signal(str)

    def __init__(self, value: str = "", placeholder: str = "",
                 provider: Callable[[], list[str]] | None = None,
                 editable: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._provider = provider or (lambda: [])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setEditable(editable)
        if placeholder and editable:
            self.combo.lineEdit().setPlaceholderText(placeholder)
        try:
            self.combo.addItems(list(self._provider()))
        except Exception:  # noqa: BLE001
            pass
        if editable:
            self.combo.setEditText(str(value or ""))
            self.combo.currentTextChanged.connect(self.changed.emit)
        else:
            idx = self.combo.findText(str(value or ""))
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
            self.combo.currentTextChanged.connect(self.changed.emit)
        layout.addWidget(self.combo, 1)

    def value(self) -> str:
        return self.combo.currentText()


class PathField(QWidget):
    """Champ chemin avec bouton « Parcourir » (fichier **ou** dossier)."""

    changed = Signal(str)

    def __init__(self, value: str = "", placeholder: str = "",
                 folder: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._folder = folder
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit(str(value or ""))
        if placeholder:
            self.edit.setPlaceholderText(placeholder)
        self.edit.textChanged.connect(self.changed.emit)
        self.btn = QPushButton("Parcourir…")
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.btn)

    def _browse(self) -> None:
        if self._folder:
            path = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier")
        if path:
            self.edit.setText(path)

    def value(self) -> str:
        return self.edit.text()
