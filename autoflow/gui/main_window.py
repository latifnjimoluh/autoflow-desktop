"""Fenêtre principale d'AutoFlow : assemble les panneaux et pilote l'exécution."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core import registry
from ..core.windows_backend import WindowsBackend
from ..hotkeys import EmergencyHotkey
from ..input_backend import InputBackend
from ..models.workflow import Schedule, Workflow
from ..persistence import store
from .action_editor import ActionEditorPanel
from .coordinate_picker import CoordinatePicker
from .log_console import LogConsole
from .param_panel import ParamPanel
from .schedule_panel import SchedulePanel
from .workflow_list import WorkflowListPanel
from .worker import ExecutorWorker


class MainWindow(QMainWindow):
    """Fenêtre principale orchestrant l'édition et l'exécution des workflows."""

    #: Émis (depuis un thread externe) pour déclencher l'arrêt d'urgence.
    emergency_stop = Signal()

    def __init__(self, autoload: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("AutoFlow — automatisation visuelle du PC")
        self.resize(1100, 720)

        self.inputs = InputBackend()
        self.windows = WindowsBackend()
        self.workflows: list[Workflow] = []
        self.current_index: int = -1

        self._thread: QThread | None = None
        self._worker: ExecutorWorker | None = None
        self._emergency = EmergencyHotkey("ctrl+shift+q", self.emergency_stop.emit)
        self._hotkey_started = False

        self._build_ui()
        self._build_toolbar()
        self._connect_signals()

        if autoload:
            self._load_workflows()
        else:
            self._new_workflow()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        """Construit les trois panneaux et la console de logs."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.workflow_panel = WorkflowListPanel()
        self.action_panel = ActionEditorPanel()
        self.right_tabs = self._build_right_panel()

        splitter.addWidget(self.workflow_panel)
        splitter.addWidget(self.action_panel)
        splitter.addWidget(self.right_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 3)
        self.setCentralWidget(splitter)

        # Console de logs en dock bas.
        self.log_console = LogConsole()
        dock = QDockWidget("Console de logs", self)
        dock.setWidget(self.log_console)
        dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea
                             | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

        # Barre de statut.
        self.status_label = QLabel("Prêt")
        self.iter_label = QLabel("Itérations : 0")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().addPermanentWidget(self.iter_label)

    def _build_right_panel(self) -> QTabWidget:
        """Construit le panneau droit à onglets (action, workflow, coordonnées)."""
        tabs = QTabWidget()

        # Onglet paramètres de l'action.
        self.param_panel = ParamPanel()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.param_panel)
        tabs.addTab(scroll, "Paramètres de l'action")

        # Onglet workflow + planning.
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

        # Onglet coordonnées.
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
        """Construit la barre d'outils (contrôles d'exécution + réglages)."""
        toolbar = QToolBar("Contrôles")
        self.addToolBar(toolbar)

        self.act_start = QAction("▶ Démarrer", self)
        self.act_pause = QAction("⏸ Pause", self)
        self.act_stop = QAction("⏹ Arrêter", self)
        self.act_save = QAction("💾 Enregistrer", self)
        self.act_pause.setEnabled(False)
        self.act_stop.setEnabled(False)
        self.act_start.triggered.connect(self._start)
        self.act_pause.triggered.connect(self._toggle_pause)
        self.act_stop.triggered.connect(self._stop)
        self.act_save.triggered.connect(self._save_current)
        for act in (self.act_start, self.act_pause, self.act_stop, self.act_save):
            toolbar.addAction(act)
        toolbar.addSeparator()

        self.failsafe_chk = QCheckBox("Failsafe")
        self.failsafe_chk.setChecked(True)
        self.failsafe_chk.toggled.connect(self.inputs.set_failsafe)
        toolbar.addWidget(self.failsafe_chk)

        toolbar.addWidget(QLabel(" Pause (s) :"))
        self.pause_spin = QDoubleSpinBox()
        self.pause_spin.setRange(0.0, 5.0)
        self.pause_spin.setSingleStep(0.05)
        self.pause_spin.setValue(0.05)
        self.pause_spin.valueChanged.connect(self.inputs.set_pause)
        toolbar.addWidget(self.pause_spin)

        toolbar.addWidget(QLabel(" Arrêt d'urgence :"))
        self.hotkey_edit = QLineEdit("ctrl+shift+q")
        self.hotkey_edit.setMaximumWidth(120)
        self.hotkey_edit.editingFinished.connect(self._update_emergency_hotkey)
        toolbar.addWidget(self.hotkey_edit)

    # ------------------------------------------------------------- signaux
    def _connect_signals(self) -> None:
        """Relie les signaux des panneaux aux gestionnaires."""
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

    # ------------------------------------------------- gestion des workflows
    def _load_workflows(self) -> None:
        """Charge les workflows depuis le disque (préchargement des exemples)."""
        store.ensure_examples()
        self.workflows = []
        for path, _name in store.list_workflows():
            try:
                self.workflows.append(store.load_workflow(path))
            except Exception as exc:  # noqa: BLE001
                self.log_console.append_log(f"Workflow ignoré ({path.name}) : {exc}",
                                            "warning")
        if not self.workflows:
            self.workflows.append(_default_workflow())
        self.current_index = 0
        self._refresh_workflow_list()
        self._refresh_current()

    def _refresh_workflow_list(self) -> None:
        names = [wf.name for wf in self.workflows]
        self.workflow_panel.set_workflows(names, self.current_index)

    def _current(self) -> Workflow | None:
        if 0 <= self.current_index < len(self.workflows):
            return self.workflows[self.current_index]
        return None

    def _select_workflow(self, index: int) -> None:
        if index < 0:
            return
        self.current_index = index
        self._refresh_current()

    def _refresh_current(self) -> None:
        """Met à jour tous les panneaux pour le workflow courant."""
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
        reponse = QMessageBox.question(
            self, "Supprimer", f"Supprimer le workflow « {wf.name} » ?")
        if reponse != QMessageBox.StandardButton.Yes:
            return
        # Supprime aussi le fichier associé s'il existe.
        path = store.workflows_dir() / f"{store.slugify(wf.name)}.json"
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
        self.log_console.append_log(f"Workflow « {wf.name} » importé.", "info")

    def _export_workflow(self) -> None:
        wf = self._current()
        if wf is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le workflow",
            f"{store.slugify(wf.name)}.json", filter="JSON (*.json)")
        if not path:
            return
        store.export_workflow(wf, path)
        self.log_console.append_log(f"Workflow exporté vers {path}.", "info")

    def _save_current(self) -> None:
        wf = self._current()
        if wf is None:
            return
        path = store.save_workflow(wf)
        self.log_console.append_log(f"Workflow enregistré ({path.name}).", "info")

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

    # --------------------------------------------------- gestion des actions
    def _select_action(self, index: int) -> None:
        wf = self._current()
        if wf is None or not (0 <= index < len(wf.actions)):
            self.param_panel.set_action(None)
            return
        self.param_panel.set_action(wf.actions[index], self._on_action_changed)

    def _on_action_changed(self) -> None:
        """Rafraîchit le résumé après modification d'un paramètre."""
        wf = self._current()
        if wf is None:
            return
        row = self.action_panel.current_row()
        self.action_panel.set_actions(wf.actions, row)

    def _add_action(self, type_name: str) -> None:
        wf = self._current()
        if wf is None:
            return
        action = registry.create_action(type_name)
        wf.actions.append(action)
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
        """Marqueur de modification (le planning a changé)."""

    # ------------------------------------------------------- coordonnées
    def _on_coordinates_captured(self, x: int, y: int) -> None:
        self._coord_value.setText(f"Dernière capture : X={x}  Y={y}")
        # Reporte dans l'action courante si elle possède des champs x/y.
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
            reponse = QMessageBox.question(
                self, "Boucle infinie",
                "Ce workflow boucle indéfiniment. Démarrer quand même ?")
            if reponse != QMessageBox.StandardButton.Yes:
                return

        self._save_current()
        self._thread = QThread(self)
        self._worker = ExecutorWorker(wf, self.inputs, self.windows)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self.log_console.append_log)
        self._worker.status.connect(self._on_status)
        self._worker.iteration.connect(self._on_iteration)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

        self.act_start.setEnabled(False)
        self.act_pause.setEnabled(True)
        self.act_stop.setEnabled(True)

    def _toggle_pause(self) -> None:
        if self._worker is None:
            return
        if self._worker.is_paused():
            self._worker.resume()
            self.act_pause.setText("⏸ Pause")
        else:
            self._worker.pause()
            self.act_pause.setText("▶ Reprendre")

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.request_stop()

    def _on_status(self, status: str) -> None:
        libelles = {"running": "En cours", "paused": "En pause", "stopped": "Arrêté"}
        self.status_label.setText(libelles.get(status, status))

    def _on_iteration(self, count: int) -> None:
        self.iter_label.setText(f"Itérations : {count}")

    def _on_finished(self, count: int) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
        self._thread = None
        self._worker = None
        self.act_start.setEnabled(True)
        self.act_pause.setEnabled(False)
        self.act_pause.setText("⏸ Pause")
        self.act_stop.setEnabled(False)
        self.status_label.setText("Prêt")

    def _on_emergency_stop(self) -> None:
        self.log_console.append_log("Arrêt d'urgence déclenché !", "error")
        self._stop()

    # ----------------------------------------------------------- réglages
    def _update_emergency_hotkey(self) -> None:
        combo = self.hotkey_edit.text().strip() or "ctrl+shift+q"
        self._emergency.stop()
        self._emergency = EmergencyHotkey(combo, self.emergency_stop.emit)
        if self._hotkey_started:
            self._emergency.start()

    # -------------------------------------------------------------- aides
    def _unique_name(self, base: str) -> str:
        noms = {wf.name for wf in self.workflows}
        if base not in noms:
            return base
        i = 2
        while f"{base} {i}" in noms:
            i += 1
        return f"{base} {i}"

    # ----------------------------------------------------------- événements
    def showEvent(self, event) -> None:  # noqa: N802 - API Qt
        super().showEvent(event)
        self.coord_picker.start()
        if not self._hotkey_started:
            self._hotkey_started = self._emergency.start()

    def closeEvent(self, event) -> None:  # noqa: N802 - API Qt
        self.coord_picker.stop()
        self._emergency.stop()
        if self._worker is not None:
            self._worker.request_stop()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
        # Sauvegarde silencieuse de tous les workflows.
        for wf in self.workflows:
            try:
                store.save_workflow(wf)
            except Exception:  # noqa: BLE001
                pass
        super().closeEvent(event)


def _default_workflow() -> Workflow:
    """Workflow vide minimal utilisé en l'absence de tout autre."""
    return Workflow(name="Nouveau workflow", schedule=Schedule(mode="run_once"))
