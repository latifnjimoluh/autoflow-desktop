"""Panneau de paramètres : formulaire **concret** généré depuis le schéma.

À partir des :class:`ParamSpec` d'une action, ce panneau construit le composant
le **plus concret possible** pour chaque champ (capture de touche, liste des
fenêtres ouvertes, sélecteur d'application, de couleur, de variable, boutons de
capture de position/région/pixel…), affiche des exemples (placeholders) et une
aide en langage simple, gère la **visibilité conditionnelle** (``depends_on``) et
propose un bouton **« Tester cette action »**.

Les *providers* (fenêtres, applications, variables, workflows, exécuteur de test)
sont optionnels : ``ParamPanel()`` sans argument reste valide (compat. tests),
les composants retombant alors sur des champs simples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..core.actions.base import Action, ParamSpec
from . import concrete_widgets as cw
from .capture_dialog import CaptureDialog


@dataclass
class PanelServices:
    """Fournisseurs branchés sur les composants concrets (tous optionnels)."""

    inputs: Any = None
    windows_provider: Callable[[], list[str]] = field(default=lambda: [])
    apps_provider: Callable[[], list[tuple[str, str]]] = field(default=lambda: [])
    variables_provider: Callable[[], list[str]] = field(default=lambda: [])
    workflows_provider: Callable[[], list[str]] = field(default=lambda: [])
    test_runner: Callable[[Action], Any] | None = None


class ParamPanel(QWidget):
    """Formulaire d'édition concret des paramètres de l'action sélectionnée."""

    def __init__(self, parent=None, services: PanelServices | None = None) -> None:
        super().__init__(parent)
        self._root = QVBoxLayout(self)
        self._form_host: QWidget | None = None
        self._action: Action | None = None
        self._on_change: Callable[[], None] = lambda: None
        self.services = services or PanelServices()
        self._controllers: set[str] = set()
        self._placeholder = QLabel("Sélectionnez une action pour la configurer.")
        self._root.addWidget(self._placeholder)
        self._root.addStretch(1)

    # -- Construction du formulaire ---------------------------------------
    def set_action(self, action: Action | None,
                   on_change: Callable[[], None] | None = None,
                   services: PanelServices | None = None) -> None:
        """Construit le formulaire concret pour ``action`` (ou le vide)."""
        if on_change is not None:
            self._on_change = on_change
        if services is not None:
            self.services = services
        self._action = action
        self._rebuild()

    def _rebuild(self) -> None:
        """(Re)génère le formulaire — appelé aussi quand un champ pilote change."""
        self._clear()
        action = self._action
        if action is None:
            self._form_layout().addWidget(QLabel("Aucune action sélectionnée."))
            return

        layout = self._form_layout()

        # En-tête : titre + aide en langage simple + bouton de test.
        title = QLabel(f"<b>{action.label or action.type_name}</b>")
        layout.addWidget(title)
        doc = (action.__doc__ or "").strip().split("\n")[0]
        if doc:
            help_label = QLabel(doc)
            help_label.setWordWrap(True)
            help_label.setProperty("variant", "muted")
            layout.addWidget(help_label)

        if self.services.test_runner is not None:
            test_btn = QPushButton("▶ Tester cette action")
            test_btn.setToolTip("Exécute uniquement cette action pour voir le résultat.")
            test_btn.setProperty("accent", "true")
            test_btn.clicked.connect(self._test_action)
            layout.addWidget(test_btn)

        layout.addWidget(_separator())

        # Détermine les paramètres pilotes (référencés par un depends_on).
        self._controllers = {
            spec.depends_on[0]
            for spec in action.param_specs() if spec.depends_on
        }

        # Champs spécifiques de l'action (avec visibilité conditionnelle).
        for spec in action.param_specs():
            if not self._depends_satisfied(spec):
                continue
            row = self._build_row(spec)
            if row is not None:
                layout.addWidget(row)

        # Boutons de capture contextuels (position / région / pixel).
        self._add_capture_buttons(action, layout)

        # Sous-actions (conditions / boucles).
        if action.child_groups():
            btn = QPushButton("✎ Modifier les sous-actions…")
            btn.clicked.connect(lambda: self._edit_children(action))
            layout.addWidget(btn)

        layout.addWidget(_separator())

        # Champs communs + section avancée (repliés en bas).
        self._add_common_fields(action, layout)
        self._add_policy_fields(action, layout)
        layout.addStretch(1)

    # -- Lignes de formulaire ---------------------------------------------
    def _build_row(self, spec: ParamSpec) -> QWidget | None:
        """Construit une ligne « libellé + widget concret » pour un paramètre."""
        widget = self._build_widget(spec)
        if widget is None:
            return None
        row = QWidget()
        box = QVBoxLayout(row)
        box.setContentsMargins(0, 2, 0, 2)
        label = QLabel(spec.label)
        if spec.help:
            label.setToolTip(spec.help)
            widget.setToolTip(spec.help)
        box.addWidget(label)
        box.addWidget(widget)
        if spec.help:
            hint = QLabel(spec.help)
            hint.setWordWrap(True)
            hint.setProperty("variant", "caption")
            box.addWidget(hint)
        return row

    def _build_widget(self, spec: ParamSpec) -> QWidget | None:
        """Crée le widget le plus concret possible selon le type du paramètre."""
        value = self._action.params.get(spec.name, spec.default)
        t = spec.type

        if t == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.toggled.connect(lambda v, n=spec.name: self._update(n, bool(v)))
            return widget

        if t == "int":
            widget = QSpinBox()
            min_v = spec.min_value if spec.min_value is not None else -1_000_000
            max_v = spec.max_value if spec.max_value is not None else 1_000_000
            widget.setRange(int(min_v), int(max_v))
            widget.setValue(int(value or 0))
            widget.valueChanged.connect(lambda v, n=spec.name: self._update(n, int(v)))
            return widget

        if t == "float":
            widget = QDoubleSpinBox()
            min_v = spec.min_value if spec.min_value is not None else -1_000_000.0
            max_v = spec.max_value if spec.max_value is not None else 1_000_000.0
            widget.setRange(float(min_v), float(max_v))
            widget.setDecimals(3)
            widget.setSingleStep(0.1)
            widget.setValue(float(value or 0.0))
            widget.valueChanged.connect(lambda v, n=spec.name: self._update(n, float(v)))
            return widget

        if t == "choice":
            widget = QComboBox()
            choices = [str(c) for c in (spec.choices or [])]
            widget.addItems(choices)
            if value is not None and str(value) in choices:
                widget.setCurrentText(str(value))
            widget.currentTextChanged.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "key":
            widget = cw.KeyCaptureField(str(value or ""), spec.placeholder)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "hotkey":
            widget = cw.HotkeyCaptureField(value, spec.placeholder)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, list(v)))
            return widget

        if t == "window":
            widget = cw.WindowSelectField(str(value or ""), spec.placeholder,
                                          self.services.windows_provider)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "app":
            widget = cw.AppSelectField(str(value or ""), spec.placeholder,
                                       self.services.apps_provider)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "color":
            widget = cw.ColorField(str(value or "#000000"))
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "variable":
            widget = cw.ComboField(str(value or ""), spec.placeholder,
                                   self.services.variables_provider)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "workflow":
            widget = cw.ComboField(str(value or ""), spec.placeholder,
                                   self.services.workflows_provider)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "folder":
            widget = cw.PathField(str(value or ""), spec.placeholder, folder=True)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "file":
            widget = cw.PathField(str(value or ""), spec.placeholder, folder=False)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, v))
            return widget

        if t == "text":
            widget = QPlainTextEdit()
            widget.setPlainText(str(value or ""))
            widget.setMaximumHeight(80)
            if spec.placeholder:
                widget.setPlaceholderText(spec.placeholder)
            widget.textChanged.connect(
                lambda w=widget, n=spec.name: self._update(n, w.toPlainText()))
            return self._maybe_wrap_vars(spec, widget, widget)

        if t == "keys":  # rétro-compatibilité : ancien type "keys"
            widget = cw.HotkeyCaptureField(value, spec.placeholder)
            widget.changed.connect(lambda v, n=spec.name: self._update(n, list(v)))
            return widget

        # Type ``str`` (et types inconnus) : champ texte avec exemple.
        widget = QLineEdit()
        widget.setText(str(value or ""))
        if spec.placeholder:
            widget.setPlaceholderText(spec.placeholder)
        widget.textChanged.connect(lambda v, n=spec.name: self._update(n, v))
        return self._maybe_wrap_vars(spec, widget, widget)

    def _maybe_wrap_vars(self, spec: ParamSpec, text_widget: QWidget,
                         editor: QWidget) -> QWidget:
        """Ajoute un bouton d'insertion de ``{{variable}}`` si le champ le permet."""
        if not spec.supports_vars:
            return text_widget
        container = QWidget()
        box = QHBoxLayout(container)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(text_widget, 1)
        btn = QToolButton()
        btn.setText("{{ }}")
        btn.setToolTip("Insérer une variable")
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(btn)
        variables = []
        try:
            variables = list(self.services.variables_provider())
        except Exception:  # noqa: BLE001
            variables = []
        for var in variables + ["date", "heure", "iteration"]:
            menu.addAction(var, lambda v=var, e=editor: self._insert_var(e, v))
        if not menu.actions():
            menu.addAction("(aucune variable)").setEnabled(False)
        btn.setMenu(menu)
        box.addWidget(btn)
        return container

    def _insert_var(self, editor: QWidget, name: str) -> None:
        """Insère ``{{name}}`` à la position du curseur du champ texte."""
        token = f"{{{{{name}}}}}"
        if isinstance(editor, QPlainTextEdit):
            editor.insertPlainText(token)
        elif isinstance(editor, QLineEdit):
            editor.insert(token)

    # -- Boutons de capture contextuels -----------------------------------
    def _add_capture_buttons(self, action: Action, layout: QVBoxLayout) -> None:
        """Ajoute les boutons « Capturer position/région/pixel » pertinents."""
        params = {s.name for s in action.param_specs()}
        buttons = QHBoxLayout()
        added = False
        if {"x", "y", "color"}.issubset(params):
            b = QPushButton("🎨 Capturer un pixel")
            b.clicked.connect(lambda: self._open_capture("pixel"))
            buttons.addWidget(b)
            added = True
        elif {"x", "y", "width", "height"}.issubset(params):
            b = QPushButton("⬚ Capturer une région")
            b.clicked.connect(lambda: self._open_capture("region"))
            buttons.addWidget(b)
            added = True
        elif {"x", "y"}.issubset(params):
            b = QPushButton("📍 Capturer une position")
            b.clicked.connect(lambda: self._open_capture("position"))
            buttons.addWidget(b)
            added = True
        if {"x1", "y1", "x2", "y2"}.issubset(params):
            b1 = QPushButton("📍 Capturer le départ")
            b1.clicked.connect(lambda: self._open_capture("position", prefix1=True))
            b2 = QPushButton("📍 Capturer l'arrivée")
            b2.clicked.connect(lambda: self._open_capture("position", prefix2=True))
            buttons.addWidget(b1)
            buttons.addWidget(b2)
            added = True
        if added:
            holder = QWidget()
            holder.setLayout(buttons)
            layout.addWidget(holder)

    def _open_capture(self, mode: str, prefix1: bool = False,
                      prefix2: bool = False) -> None:
        """Ouvre le dialogue de capture et applique les valeurs récupérées."""
        if self._action is None:
            return
        dialog = CaptureDialog(self.services.inputs, mode=mode, parent=self)
        if dialog.exec() and dialog.result_value:
            values = dialog.result_value
            if prefix1:
                self._action.params["x1"] = values.get("x", 0)
                self._action.params["y1"] = values.get("y", 0)
            elif prefix2:
                self._action.params["x2"] = values.get("x", 0)
                self._action.params["y2"] = values.get("y", 0)
            else:
                for key, val in values.items():
                    self._action.params[key] = val
            self._on_change()
            self._rebuild()

    # -- Champs communs & avancés -----------------------------------------
    def _add_common_fields(self, action: Action, layout: QVBoxLayout) -> None:
        row = QWidget()
        box = QHBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        chk = QCheckBox("Action activée")
        chk.setChecked(action.enabled)
        chk.toggled.connect(self._set_enabled)
        box.addWidget(chk)
        box.addWidget(QLabel("Délai après (s) :"))
        delay = QDoubleSpinBox()
        delay.setRange(0.0, 86400.0)
        delay.setDecimals(2)
        delay.setSingleStep(0.1)
        delay.setValue(float(action.delay_after))
        delay.valueChanged.connect(self._set_delay)
        box.addWidget(delay)
        box.addStretch(1)
        layout.addWidget(row)

    def _add_policy_fields(self, action: Action, layout: QVBoxLayout) -> None:
        """Section « avancé » : ré-essais et comportement en cas d'échec."""
        advanced = QToolButton()
        advanced.setText("⚙ Options avancées (ré-essais, erreurs, aléa)")
        advanced.setCheckable(True)
        advanced.setStyleSheet("text-align: left;")
        panel = QWidget()
        panel.setVisible(False)
        grid = QVBoxLayout(panel)

        def add_field(label: str, widget: QWidget) -> None:
            line = QHBoxLayout()
            line.addWidget(QLabel(label))
            line.addWidget(widget, 1)
            holder = QWidget()
            holder.setLayout(line)
            grid.addWidget(holder)

        retries = QSpinBox()
        retries.setRange(0, 100)
        retries.setValue(int(action.retries))
        retries.valueChanged.connect(
            lambda v: setattr(action, "retries", int(v)) or self._on_change())
        add_field("Ré-essais", retries)

        retry_delay = QDoubleSpinBox()
        retry_delay.setRange(0.0, 3600.0)
        retry_delay.setDecimals(2)
        retry_delay.setValue(float(action.retry_delay))
        retry_delay.valueChanged.connect(
            lambda v: setattr(action, "retry_delay", float(v)) or self._on_change())
        add_field("Délai entre essais (s)", retry_delay)

        on_error = QComboBox()
        on_error.addItems(["inherit", "continue", "stop"])
        on_error.setCurrentText(action.on_error)
        on_error.currentTextChanged.connect(
            lambda v: setattr(action, "on_error", v) or self._on_change())
        add_field("En cas d'échec", on_error)

        jitter = QDoubleSpinBox()
        jitter.setRange(0.0, 60.0)
        jitter.setDecimals(2)
        jitter.setValue(float(action.delay_jitter))
        jitter.valueChanged.connect(
            lambda v: setattr(action, "delay_jitter", float(v)) or self._on_change())
        add_field("Aléa de délai « humain » (s)", jitter)

        advanced.toggled.connect(panel.setVisible)
        layout.addWidget(advanced)
        layout.addWidget(panel)

    # -- Test d'action -----------------------------------------------------
    def _test_action(self) -> None:
        """Exécute uniquement l'action en cours et affiche le résultat."""
        if self._action is None or self.services.test_runner is None:
            return
        result = self.services.test_runner(self._action)
        ok = getattr(result, "ok", False)
        message = getattr(result, "message", lambda: str(result))()
        if ok:
            QMessageBox.information(self, "Test de l'action", "✅ " + message)
        else:
            QMessageBox.warning(self, "Test de l'action", "⚠ " + message)

    def _edit_children(self, action: Action) -> None:
        from .child_editor import ChildEditorDialog

        ChildEditorDialog(action, self).exec()
        self._on_change()

    # -- Mises à jour ------------------------------------------------------
    def _depends_satisfied(self, spec: ParamSpec) -> bool:
        """Indique si la dépendance conditionnelle d'un champ est satisfaite."""
        if not spec.depends_on or self._action is None:
            return True
        name, expected = spec.depends_on
        if name not in self._action.params:
            return True  # paramètre pilote absent : on n'masque pas (sécurité)
        actual = self._action.params.get(name)
        if isinstance(expected, (tuple, list)):
            return actual in expected
        return actual == expected

    def _update(self, name: str, value: Any) -> None:
        if self._action is not None:
            self._action.params[name] = value
            self._on_change()
            if name in self._controllers:
                self._rebuild()  # un champ pilote a changé : on réadapte le formulaire

    def _set_enabled(self, value: bool) -> None:
        if self._action is not None:
            self._action.enabled = bool(value)
            self._on_change()

    def _set_delay(self, value: float) -> None:
        if self._action is not None:
            self._action.delay_after = float(value)
            self._on_change()

    # -- Infrastructure ----------------------------------------------------
    def _form_layout(self) -> QVBoxLayout:
        """Renvoie le layout hôte du formulaire (créé à la volée)."""
        if self._form_host is None:
            self._form_host = QWidget()
            QVBoxLayout(self._form_host)
            self._root.insertWidget(0, self._form_host)
        return self._form_host.layout()

    def _clear(self) -> None:
        if self._form_host is not None:
            self._form_host.deleteLater()
            self._form_host = None
        self._placeholder.hide()

    # -- Compatibilité ascendante (ancien attribut interne ``_layout``) ----
    @property
    def _layout(self):  # pragma: no cover - utilisé par d'anciens tests
        """Expose un objet exposant ``rowCount()`` pour les tests historiques."""
        host = self._form_layout()
        return _LayoutShim(host)


class _LayoutShim:
    """Adaptateur minimal : ``rowCount()`` = nombre de widgets du formulaire."""

    def __init__(self, layout: QVBoxLayout) -> None:
        self._layout = layout

    def rowCount(self) -> int:  # noqa: N802 - imite l'API QFormLayout
        return self._layout.count()

    def count(self) -> int:
        return self._layout.count()


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
