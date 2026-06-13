"""Fenêtre principale d'AutoFlow : assemble les panneaux et pilote l'exécution."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import autostart
from ..core import registry
from ..core.export_python import export_to_file
from ..core.history import HistoryDB, default_history_path
from ..core.windows_backend import WindowsBackend
from ..hotkeys import EmergencyHotkey, GlobalHotkeyManager
from ..input_backend import InputBackend
from ..models.workflow import Schedule, Workflow
from ..persistence import profiles, store
from ..settings import load_settings, save_settings
from .action_editor import ActionEditorPanel
from .coordinate_picker import CoordinatePicker
from .history_dialog import HistoryDialog
from .log_console import LogConsole
from .param_panel import ParamPanel
from .schedule_panel import SchedulePanel
from .settings_dialog import SettingsDialog
from .theme import apply_theme, tr
from .workflow_list import WorkflowListPanel
from .worker import ExecutorWorker


class MainWindow(QMainWindow):
    """Fenêtre principale orchestrant l'édition et l'exécution des workflows."""

    emergency_stop = Signal()
    trigger_workflow = Signal(str)

    def __init__(self, autoload: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("AutoFlow — automatisation visuelle du PC")
        self.resize(1180, 760)

        self.settings = load_settings()
        self.inputs = InputBackend(failsafe=self.settings.failsafe,
                                   pause=self.settings.pyautogui_pause)
        self.windows = WindowsBackend()
        self.history = HistoryDB(default_history_path())
        self.workflows: list[Workflow] = []
        self.current_index: int = -1
        self.active_profile = self.settings.active_profile

        self._thread: QThread | None = None
        self._worker: ExecutorWorker | None = None
        self._run_started_at: datetime | None = None
        self._emergency = EmergencyHotkey(self.settings.emergency_hotkey,
                                          self.emergency_stop.emit)
        self._wf_hotkeys = GlobalHotkeyManager()
        self._hotkey_started = False
        self._force_quit = False

        self._build_ui()
        self._build_toolbar()
        self._build_tray()
        self._connect_signals()

        if autoload:
            self._load_workflows()
        else:
            self._new_workflow()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workflow_panel = WorkflowListPanel()
        self.action_panel = ActionEditorPanel()
        self.center_widget = self._build_center_panel()
        self.right_tabs = self._build_right_panel()
        splitter.addWidget(self.workflow_panel)
        splitter.addWidget(self.center_widget)
        splitter.addWidget(self.right_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 3)
        self.setCentralWidget(splitter)

        self.log_console = LogConsole()
        dock = QDockWidget("Console de logs", self)
        dock.setWidget(self.log_console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

        self.status_label = QLabel("Prêt")
        self.iter_label = QLabel("Itérations : 0")
        self.var_label = QLabel("")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().addWidget(self.var_label, 1)
        self.statusBar().addPermanentWidget(self.iter_label)

    def _build_center_panel(self) -> QWidget:
        """Zone centrale : bascule entre vue Liste et vue Nœuds (n8n)."""
        from PySide6.QtWidgets import QButtonGroup, QPushButton, QStackedWidget

        from .node_view import NodeView

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        switch = QHBoxLayout()
        self._btn_list_view = QPushButton("≣ Liste")
        self._btn_node_view = QPushButton("🔗 Schéma (nœuds)")
        for btn in (self._btn_list_view, self._btn_node_view):
            btn.setCheckable(True)
        self._btn_list_view.setChecked(True)
        group = QButtonGroup(container)
        group.setExclusive(True)
        group.addButton(self._btn_list_view)
        group.addButton(self._btn_node_view)
        switch.addWidget(self._btn_list_view)
        switch.addWidget(self._btn_node_view)
        switch.addStretch(1)
        layout.addLayout(switch)

        self._views = QStackedWidget()
        self.node_view = NodeView()
        self._views.addWidget(self.action_panel)   # index 0 : liste
        self._views.addWidget(self.node_view)       # index 1 : nœuds
        layout.addWidget(self._views)

        self._btn_list_view.clicked.connect(lambda: self._set_view(0))
        self._btn_node_view.clicked.connect(lambda: self._set_view(1))

        self.node_view.action_selected.connect(self._on_node_selected)
        self.node_view.edit_requested.connect(self._on_node_selected)
        self.node_view.insert_requested.connect(self._on_node_insert)
        return container

    def _set_view(self, index: int) -> None:
        """Bascule entre la vue Liste (0) et la vue Nœuds (1)."""
        self._views.setCurrentIndex(index)
        if index == 1:
            self._refresh_node_view()

    def _refresh_node_view(self) -> None:
        wf = self._current()
        if wf is not None:
            self.node_view.set_actions(wf.actions, self.action_panel.current_row())

    def _on_node_selected(self, index: int) -> None:
        """Sélectionne une action depuis la vue en nœuds et l'édite."""
        wf = self._current()
        if wf is None or not (0 <= index < len(wf.actions)):
            return
        self.action_panel.list.setCurrentRow(index)
        self._select_action(index)
        self.right_tabs.setCurrentIndex(0)  # onglet « Paramètres »

    def _on_node_insert(self, position: int) -> None:
        """Insère une action à la position choisie via la palette surgissante."""
        from .action_palette import ActionPaletteDialog

        wf = self._current()
        if wf is None:
            return
        dialog = ActionPaletteDialog(self)
        if dialog.exec() and dialog.chosen_type:
            position = max(0, min(position, len(wf.actions)))
            wf.actions.insert(position, registry.create_action(dialog.chosen_type))
            self._refresh_action_list(select=position)

    def _build_right_panel(self) -> QTabWidget:
        tabs = QTabWidget()
        self.param_panel = ParamPanel(services=self._panel_services())
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.param_panel)
        tabs.addTab(scroll, "Paramètres de l'action")

        wf_tab = QWidget()
        wf_layout = QFormLayout(wf_tab)
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._rename_workflow)
        self.desc_edit = QLineEdit()
        self.desc_edit.editingFinished.connect(self._update_description)
        wf_layout.addRow("Nom", self.name_edit)
        wf_layout.addRow("Description", self.desc_edit)
        self.schedule_panel = SchedulePanel()
        wf_layout.addRow(self.schedule_panel)
        tabs.addTab(wf_tab, "Workflow & planning")

        coord_tab = QWidget()
        coord_layout = QVBoxLayout(coord_tab)
        self.coord_picker = CoordinatePicker(self.inputs)
        coord_layout.addWidget(QLabel(
            "Survolez l'écran : la position s'affiche en direct.\n"
            "Cliquez « Capturer » pour copier les coordonnées."))
        coord_layout.addWidget(self.coord_picker)
        self._coord_value = QLabel("Dernière capture : —")
        coord_layout.addWidget(self._coord_value)
        coord_layout.addStretch(1)
        tabs.addTab(coord_tab, "Coordonnées")
        return tabs

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Contrôles")
        self.addToolBar(toolbar)
        lang = self.settings.language

        self.act_start = QAction(tr("start", lang), self)
        self.act_pause = QAction(tr("pause", lang), self)
        self.act_stop = QAction(tr("stop", lang), self)
        self.act_step = QAction(tr("step", lang), self)
        self.act_save = QAction(tr("save", lang), self)
        self.act_pause.setEnabled(False)
        self.act_stop.setEnabled(False)
        self.act_step.setEnabled(False)
        self.act_start.triggered.connect(self._start)
        self.act_pause.triggered.connect(self._toggle_pause)
        self.act_stop.triggered.connect(self._stop)
        self.act_step.triggered.connect(self._do_step)
        self.act_save.triggered.connect(self._save_current)
        for act in (self.act_start, self.act_pause, self.act_step, self.act_stop, self.act_save):
            toolbar.addAction(act)
        # Met en valeur le bouton « Démarrer » (couleur de succès).
        start_btn = toolbar.widgetForAction(self.act_start)
        if start_btn is not None:
            start_btn.setStyleSheet(
                "QToolButton { background:#2ea043; color:#fff; border:none;"
                " border-radius:7px; padding:6px 14px; font-weight:600; }"
                "QToolButton:hover { background:#3fb950; }"
                "QToolButton:disabled { background:#3a3d47; color:#8a90a0; }")

        self.step_chk = QCheckBox("Pas à pas")
        toolbar.addWidget(self.step_chk)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel(f" {tr('profile', lang)} :"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(120)
        self.profile_combo.currentTextChanged.connect(self._change_profile)
        toolbar.addWidget(self.profile_combo)
        self._btn_new_profile = QAction("➕ Profil", self)
        self._btn_new_profile.triggered.connect(self._new_profile)
        toolbar.addAction(self._btn_new_profile)
        toolbar.addSeparator()

        act_gallery = QAction("📚 Galerie de modèles", self)
        act_gallery.triggered.connect(self._open_gallery)
        act_wizard = QAction("🧭 Assistant", self)
        act_wizard.triggered.connect(self._run_wizard)
        toolbar.addAction(act_wizard)
        act_settings = QAction(tr("settings", lang), self)
        act_settings.triggered.connect(self._open_settings)
        act_history = QAction(tr("history", lang), self)
        act_history.triggered.connect(self._open_history)
        act_export_py = QAction(tr("export_py", lang), self)
        act_export_py.triggered.connect(self._export_python)
        for act in (act_gallery, act_settings, act_history, act_export_py):
            toolbar.addAction(act)

    def _build_tray(self) -> None:
        """Crée l'icône de la barre des tâches (si disponible)."""
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("AutoFlow")
        menu = QMenu()
        lang = self.settings.language
        act_show = menu.addAction(tr("show", lang))
        act_show.triggered.connect(self._restore_window)
        act_start = menu.addAction(tr("start", lang))
        act_start.triggered.connect(self._start)
        act_stop = menu.addAction(tr("stop", lang))
        act_stop.triggered.connect(self._stop)
        menu.addSeparator()
        act_quit = menu.addAction(tr("quit", lang))
        act_quit.triggered.connect(self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self._restore_window()
            if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    # ------------------------------------------------------------- signaux
    def _connect_signals(self) -> None:
        self.workflow_panel.selected.connect(self._select_workflow)
        self.workflow_panel.new_requested.connect(self._new_workflow)
        self.workflow_panel.duplicate_requested.connect(self._duplicate_workflow)
        self.workflow_panel.delete_requested.connect(self._delete_workflow)
        self.workflow_panel.import_requested.connect(self._import_workflow)
        self.workflow_panel.export_requested.connect(self._export_workflow)

        self.action_panel.selected.connect(self._select_action)
        self.action_panel.add_requested.connect(self._add_action)
        self.action_panel.remove_requested.connect(self._remove_action)
        self.action_panel.move_up_requested.connect(lambda: self._move_action(-1))
        self.action_panel.move_down_requested.connect(lambda: self._move_action(1))
        self.action_panel.toggle_requested.connect(self._toggle_action)

        self.coord_picker.captured.connect(self._on_coordinates_captured)
        self.emergency_stop.connect(self._on_emergency_stop)
        self.trigger_workflow.connect(self._on_trigger_workflow)

    # ------------------------------------------------- gestion des workflows
    def _workflows_dir(self):
        return profiles.profile_workflows_dir(self.active_profile)

    def _load_workflows(self) -> None:
        directory = self._workflows_dir()
        store.ensure_examples(directory)
        self.workflows = []
        for path, _name in store.list_workflows(directory):
            try:
                self.workflows.append(store.load_workflow(path))
            except Exception as exc:  # noqa: BLE001
                self.log_console.append_log(f"Workflow ignoré ({path.name}) : {exc}",
                                            "warning")
        if not self.workflows:
            self.workflows.append(_default_workflow())
        self.current_index = 0
        self._refresh_profile_combo()
        self._refresh_workflow_list()
        self._refresh_current()
        self._register_workflow_hotkeys()

    def _refresh_profile_combo(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles.list_profiles())
        self.profile_combo.setCurrentText(self.active_profile)
        self.profile_combo.blockSignals(False)

    def _refresh_workflow_list(self) -> None:
        names = [wf.name for wf in self.workflows]
        self.workflow_panel.set_workflows(names, self.current_index)

    def _current(self) -> Workflow | None:
        if 0 <= self.current_index < len(self.workflows):
            return self.workflows[self.current_index]
        return None

    def _resolve_workflow(self, name: str) -> Workflow | None:
        for wf in self.workflows:
            if wf.name == name:
                return wf
        return None

    def _select_workflow(self, index: int) -> None:
        if index < 0:
            return
        self.current_index = index
        self._refresh_current()

    def _refresh_current(self) -> None:
        wf = self._current()
        if wf is None:
            return
        self.name_edit.setText(wf.name)
        self.desc_edit.setText(wf.description)
        self.schedule_panel.set_schedule(wf.schedule, self._touch)
        self._refresh_action_list(select=0 if wf.actions else -1)

    def _refresh_action_list(self, select: int = -1) -> None:
        wf = self._current()
        if wf is None:
            return
        self.action_panel.set_actions(wf.actions, select)
        if getattr(self, "_views", None) is not None and self._views.currentIndex() == 1:
            self.node_view.set_actions(wf.actions, select)
        self._select_action(select)

    def _new_workflow(self) -> None:
        wf = Workflow(name=self._unique_name("Nouveau workflow"),
                      schedule=Schedule(mode="run_once"))
        self.workflows.append(wf)
        self.current_index = len(self.workflows) - 1
        self._refresh_workflow_list()
        self._refresh_current()

    def _duplicate_workflow(self) -> None:
        wf = self._current()
        if wf is None:
            return
        clone = Workflow.from_dict(wf.to_dict())
        clone.name = self._unique_name(f"{wf.name} (copie)")
        self.workflows.append(clone)
        self.current_index = len(self.workflows) - 1
        self._refresh_workflow_list()
        self._refresh_current()

    def _delete_workflow(self) -> None:
        wf = self._current()
        if wf is None:
            return
        if QMessageBox.question(self, "Supprimer",
                                f"Supprimer le workflow « {wf.name} » ?") \
                != QMessageBox.StandardButton.Yes:
            return
        path = self._workflows_dir() / f"{store.slugify(wf.name)}.json"
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        del self.workflows[self.current_index]
        if not self.workflows:
            self.workflows.append(_default_workflow())
        self.current_index = max(0, self.current_index - 1)
        self._refresh_workflow_list()
        self._refresh_current()

    def _import_workflow(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importer un workflow",
                                              filter="JSON (*.json)")
        if not path:
            return
        try:
            wf = store.import_workflow(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Import", f"Import impossible : {exc}")
            return
        wf.name = self._unique_name(wf.name)
        self.workflows.append(wf)
        self.current_index = len(self.workflows) - 1
        self._refresh_workflow_list()
        self._refresh_current()

    def _export_workflow(self) -> None:
        wf = self._current()
        if wf is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le workflow",
            f"{store.slugify(wf.name)}.json", filter="JSON (*.json)")
        if path:
            store.export_workflow(wf, path)
            self.log_console.append_log(f"Workflow exporté vers {path}.", "info")

    def _export_python(self) -> None:
        wf = self._current()
        if wf is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en script Python",
            f"{store.slugify(wf.name)}.py", filter="Python (*.py)")
        if path:
            export_to_file(wf, path)
            self.log_console.append_log(f"Script Python généré : {path}.", "info")

    def _save_current(self) -> None:
        wf = self._current()
        if wf is None:
            return
        path = store.save_workflow(wf, self._workflows_dir() / f"{store.slugify(wf.name)}.json")
        self.log_console.append_log(f"Workflow enregistré ({path.name}).", "info")
        self._register_workflow_hotkeys()

    def _rename_workflow(self) -> None:
        wf = self._current()
        if wf is None:
            return
        new_name = self.name_edit.text().strip()
        if new_name and new_name != wf.name:
            wf.name = new_name
            self._refresh_workflow_list()

    def _update_description(self) -> None:
        wf = self._current()
        if wf is not None:
            wf.description = self.desc_edit.text()

    # ----------------------------------------------------------- profils
    def _change_profile(self, name: str) -> None:
        if not name or name == self.active_profile:
            return
        self.active_profile = name
        self.settings.active_profile = name
        save_settings(self.settings)
        self._load_workflows()

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Nouveau profil", "Nom du profil :")
        if ok and name.strip():
            profiles.create_profile(name.strip())
            self.active_profile = name.strip()
            self.settings.active_profile = self.active_profile
            save_settings(self.settings)
            self._load_workflows()

    # --------------------------------------------------- gestion des actions
    def _panel_services(self):
        """Construit les fournisseurs concrets branchés sur le panneau de params."""
        from ..services import list_installed_apps, list_open_windows, test_action
        from ..services.windows_list import window_titles
        from .param_panel import PanelServices

        def variables_provider() -> list[str]:
            names: list[str] = []
            if self._worker is not None:
                names = list(self._worker.executor.variables.as_dict().keys())
            wf = self._current()
            if wf is not None:
                for act in wf.actions:
                    for key in ("name", "var_name", "output_var"):
                        val = str(act.params.get(key, "")).strip()
                        if val and val not in names:
                            names.append(val)
            return names

        def apps_provider() -> list[tuple[str, str]]:
            return [(a.name, a.path) for a in list_installed_apps()]

        def workflows_provider() -> list[str]:
            return [wf.name for wf in self.workflows]

        def runner(action):
            return test_action(action, self.inputs, self.windows,
                               settings=self.settings,
                               workflow_resolver=self._resolve_workflow)

        return PanelServices(
            inputs=self.inputs,
            windows_provider=window_titles,
            apps_provider=apps_provider,
            variables_provider=variables_provider,
            workflows_provider=workflows_provider,
            test_runner=runner,
        )

    def _select_action(self, index: int) -> None:
        wf = self._current()
        if wf is None or not (0 <= index < len(wf.actions)):
            self.param_panel.set_action(None)
            return
        self.param_panel.set_action(wf.actions[index], self._on_action_changed)

    def _on_action_changed(self) -> None:
        wf = self._current()
        if wf is None:
            return
        row = self.action_panel.current_row()
        self.action_panel.set_actions(wf.actions, row)
        if getattr(self, "_views", None) is not None and self._views.currentIndex() == 1:
            self.node_view.set_actions(wf.actions, row)

    def _add_action(self, type_name: str) -> None:
        wf = self._current()
        if wf is None:
            return
        wf.actions.append(registry.create_action(type_name))
        self._refresh_action_list(select=len(wf.actions) - 1)

    def _remove_action(self) -> None:
        wf = self._current()
        row = self.action_panel.current_row()
        if wf is None or not (0 <= row < len(wf.actions)):
            return
        del wf.actions[row]
        self._refresh_action_list(select=min(row, len(wf.actions) - 1))

    def _move_action(self, delta: int) -> None:
        wf = self._current()
        row = self.action_panel.current_row()
        if wf is None or not (0 <= row < len(wf.actions)):
            return
        new_row = row + delta
        if not (0 <= new_row < len(wf.actions)):
            return
        wf.actions[row], wf.actions[new_row] = wf.actions[new_row], wf.actions[row]
        self._refresh_action_list(select=new_row)

    def _toggle_action(self) -> None:
        wf = self._current()
        row = self.action_panel.current_row()
        if wf is None or not (0 <= row < len(wf.actions)):
            return
        wf.actions[row].enabled = not wf.actions[row].enabled
        self._refresh_action_list(select=row)

    def _touch(self) -> None:
        """Marqueur de modification du planning."""
        self._register_workflow_hotkeys()

    # ------------------------------------------------------- coordonnées
    def _on_coordinates_captured(self, x: int, y: int) -> None:
        self._coord_value.setText(f"Dernière capture : X={x}  Y={y}")
        wf = self._current()
        row = self.action_panel.current_row()
        if wf is not None and 0 <= row < len(wf.actions):
            action = wf.actions[row]
            if "x" in action.params and "y" in action.params:
                action.params["x"] = x
                action.params["y"] = y
                self.param_panel.set_action(action, self._on_action_changed)
                self._on_action_changed()

    # ----------------------------------------------------------- exécution
    def _start(self) -> None:
        if self._thread is not None:
            return
        wf = self._current()
        if wf is None:
            return
        if not wf.enabled_actions():
            QMessageBox.information(self, "Exécution",
                                    "Ce workflow ne contient aucune action activée.")
            return
        if wf.schedule.mode == "loop_interval" and wf.schedule.max_iterations <= 0:
            if QMessageBox.question(
                    self, "Boucle infinie",
                    "Ce workflow boucle indéfiniment. Démarrer quand même ?") \
                    != QMessageBox.StandardButton.Yes:
                return

        self._save_current()
        self._run_started_at = datetime.now()
        self._thread = QThread(self)
        self._worker = ExecutorWorker(
            wf, self.inputs, self.windows, settings=self.settings,
            workflow_resolver=self._resolve_workflow,
            step_mode=self.step_chk.isChecked())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self.log_console.append_log)
        self._worker.status.connect(self._on_status)
        self._worker.iteration.connect(self._on_iteration)
        self._worker.action_at.connect(self._on_action_at)
        self._worker.step_at.connect(self._on_action_at)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

        self.act_start.setEnabled(False)
        self.act_pause.setEnabled(True)
        self.act_stop.setEnabled(True)
        self.act_step.setEnabled(self.step_chk.isChecked())
        self._notify("AutoFlow", f"Démarrage de « {wf.name} ».")

    def _toggle_pause(self) -> None:
        if self._worker is None:
            return
        if self._worker.is_paused():
            self._worker.resume()
            self.act_pause.setText(tr("pause", self.settings.language))
        else:
            self._worker.pause()
            self.act_pause.setText("▶ Reprendre")

    def _do_step(self) -> None:
        if self._worker is not None:
            self._worker.step()

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.request_stop()

    def _on_status(self, status: str) -> None:
        self.status_label.setText(tr(status, self.settings.language))

    def _on_iteration(self, count: int) -> None:
        self.iter_label.setText(f"Itérations : {count}")

    def _on_action_at(self, action, _iteration: int) -> None:
        """Surligne l'action en cours et affiche l'état des variables."""
        wf = self._current()
        if wf is not None:
            try:
                row = wf.actions.index(action)
                self.action_panel.list.setCurrentRow(row)
            except ValueError:
                pass  # action imbriquée : non surlignable au niveau racine
        if self._worker is not None:
            variables = self._worker.executor.variables.as_dict()
            apercu = ", ".join(f"{k}={v}" for k, v in list(variables.items())[:6])
            self.var_label.setText(f"Variables : {apercu}")

    def _on_finished(self, count: int) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
        wf = self._current()
        if wf is not None and self._run_started_at is not None:
            try:
                self.history.record_run(wf.name, self._run_started_at,
                                        datetime.now(), success=True, iterations=count)
            except Exception:  # noqa: BLE001
                pass
            self._notify("AutoFlow", f"« {wf.name} » terminé ({count} itération(s)).")
        self._thread = None
        self._worker = None
        self.act_start.setEnabled(True)
        self.act_pause.setEnabled(False)
        self.act_pause.setText(tr("pause", self.settings.language))
        self.act_step.setEnabled(False)
        self.act_stop.setEnabled(False)
        self.status_label.setText(tr("ready", self.settings.language))

    def _on_emergency_stop(self) -> None:
        self.log_console.append_log("Arrêt d'urgence déclenché !", "error")
        self._notify("AutoFlow", "Arrêt d'urgence déclenché.", "error")
        self._stop()

    def _on_trigger_workflow(self, name: str) -> None:
        """Démarre le workflow associé à un raccourci global."""
        for i, wf in enumerate(self.workflows):
            if wf.name == name:
                self.current_index = i
                self._refresh_workflow_list()
                self._refresh_current()
                self._start()
                return

    # ----------------------------------------------------------- réglages
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.result_settings()
            save_settings(self.settings)
            self.inputs.set_failsafe(self.settings.failsafe)
            self.inputs.set_pause(self.settings.pyautogui_pause)
            self._apply_theme()
            self._apply_autostart()
            self._restart_emergency_hotkey()
            self.log_console.append_log("Réglages enregistrés.", "info")

    def _open_history(self) -> None:
        HistoryDialog(self.history, self).exec()

    def _maybe_onboard(self) -> None:
        """Affiche l'écran d'accueil au tout premier lancement."""
        if self.settings.onboarded:
            return
        self.settings.onboarded = True
        save_settings(self.settings)
        from .onboarding import WelcomeDialog

        welcome = WelcomeDialog(self)
        if not welcome.exec() or welcome.choice is None:
            return
        if welcome.choice == WelcomeDialog.GALLERY:
            self._open_gallery()
        elif welcome.choice == WelcomeDialog.WIZARD:
            self._run_wizard()
        elif welcome.choice == WelcomeDialog.SCRATCH:
            self._new_workflow()

    def _run_wizard(self) -> None:
        """Lance l'assistant de création guidée d'un workflow."""
        from .onboarding import CreationWizard

        wizard = CreationWizard(self)
        if wizard.exec():
            wf = wizard.build_workflow()
            wf.name = self._unique_name(wf.name)
            self.workflows.append(wf)
            self.current_index = len(self.workflows) - 1
            self._refresh_workflow_list()
            self._refresh_current()
            self.log_console.append_log(
                f"Workflow « {wf.name} » créé via l'assistant.", "info")

    def _open_gallery(self) -> None:
        """Ouvre la galerie de modèles et clone le modèle choisi."""
        from .template_gallery import TemplateGallery

        gallery = TemplateGallery(self)
        if gallery.exec() and gallery.selected_template is not None:
            wf = gallery.selected_template.to_workflow()
            wf.name = self._unique_name(wf.name)
            self.workflows.append(wf)
            self.current_index = len(self.workflows) - 1
            self._refresh_workflow_list()
            self._refresh_current()
            self.log_console.append_log(
                f"Modèle « {wf.name} » ajouté à vos workflows.", "info")

    def _apply_theme(self) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self.settings.theme)

    def _apply_autostart(self) -> None:
        if self.settings.autostart:
            autostart.enable()
        else:
            autostart.disable()

    def _restart_emergency_hotkey(self) -> None:
        self._emergency.stop()
        self._emergency = EmergencyHotkey(self.settings.emergency_hotkey,
                                          self.emergency_stop.emit)
        if self._hotkey_started:
            self._emergency.start()

    def _register_workflow_hotkeys(self) -> None:
        """(Ré)enregistre les raccourcis globaux par workflow déclenchable."""
        bindings = {}
        for wf in self.workflows:
            if wf.schedule.mode == "hotkey_trigger" and wf.schedule.hotkey:
                bindings[wf.schedule.hotkey] = (
                    lambda name=wf.name: self.trigger_workflow.emit(name))
        if self._hotkey_started:
            self._wf_hotkeys.set_bindings(bindings)
        else:
            self._wf_hotkeys._bindings = bindings

    def _notify(self, title: str, message: str, level: str = "info") -> None:
        if self.settings.notifications and self.tray is not None:
            icon = (QSystemTrayIcon.MessageIcon.Critical if level == "error"
                    else QSystemTrayIcon.MessageIcon.Information)
            self.tray.showMessage(title, message, icon, 3000)

    # -------------------------------------------------------------- aides
    def _unique_name(self, base: str) -> str:
        noms = {wf.name for wf in self.workflows}
        if base not in noms:
            return base
        i = 2
        while f"{base} {i}" in noms:
            i += 1
        return f"{base} {i}"

    def _restore_window(self) -> None:
        self.showNormal()
        self.activateWindow()

    def _quit(self) -> None:
        self._force_quit = True
        self.close()

    # ----------------------------------------------------------- événements
    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.coord_picker.start()
        if not self._hotkey_started:
            self._hotkey_started = self._emergency.start()
            self._register_workflow_hotkeys()
            self._wf_hotkeys.restart()
        self._apply_theme()
        if not self.settings.onboarded:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(0, self._maybe_onboard)

    def closeEvent(self, event) -> None:  # noqa: N802
        # Réduction dans la barre des tâches plutôt que fermeture.
        if not self._force_quit and self.settings.minimize_to_tray and self.tray is not None:
            event.ignore()
            self.hide()
            self._notify("AutoFlow", "Application réduite dans la barre des tâches.")
            return
        self.coord_picker.stop()
        self._emergency.stop()
        self._wf_hotkeys.stop()
        if self._worker is not None:
            self._worker.request_stop()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
        for wf in self.workflows:
            try:
                store.save_workflow(wf, self._workflows_dir() / f"{store.slugify(wf.name)}.json")
            except Exception:  # noqa: BLE001
                pass
        try:
            self.history.close()
        except Exception:  # noqa: BLE001
            pass
        super().closeEvent(event)


def _default_workflow() -> Workflow:
    return Workflow(name="Nouveau workflow", schedule=Schedule(mode="run_once"))
