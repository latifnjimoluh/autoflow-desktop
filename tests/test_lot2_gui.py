"""Lot 2 — smoke GUI (offscreen) : tableau de bord, palette, déclencheurs."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from autoflow.core import registry  # noqa: E402
from autoflow.core.history import HistoryDB  # noqa: E402
from autoflow.models.workflow import Schedule, Workflow  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_dashboard_se_construit(app):
    from autoflow.gui.dashboard import DashboardWidget

    db = HistoryDB(":memory:")
    from datetime import datetime
    db.record_run("WF", datetime(2026, 1, 1, 8), datetime(2026, 1, 1, 8, 0, 5),
                  True, 1)
    workflows = [Workflow(name="WF", schedule=Schedule(mode="loop_interval"))]
    widget = DashboardWidget(db, lambda: workflows)
    widget.refresh()
    assert widget.table.rowCount() == 1
    db.close()


def test_command_palette_filtre(app):
    from autoflow.gui.command_palette import Command, CommandPalette

    fired = []
    commands = [
        Command("Exécuter A", lambda: fired.append("A"), "Workflow"),
        Command("Exécuter B", lambda: fired.append("B"), "Workflow"),
    ]
    palette = CommandPalette(commands)
    assert palette.list.count() == 2
    palette.search.setText("B")
    assert palette.list.count() == 1
    palette._run_current()
    assert fired == ["B"]


def test_command_palette_build_default(app):
    from autoflow.gui.command_palette import build_default_commands

    workflows = [Workflow(name="Alpha"), Workflow(name="Beta")]
    cmds = build_default_commands(workflows, lambda n: None)
    assert len(cmds) == 2
    assert "Alpha" in cmds[0].label


def test_triggers_dialog_ajoute_et_serialise(app):
    from autoflow.gui.triggers_dialog import TriggersDialog

    dialog = TriggersDialog([])
    dialog._type_combo.setCurrentIndex(0)
    dialog._add()
    result = dialog.result_triggers()
    assert len(result) == 1
    assert "type" in result[0]
    # Le déclencheur reconstruit est valide.
    registry  # noqa: B018 - garde l'import (registre peuplé)
    from autoflow.core.triggers import trigger_from_dict
    assert trigger_from_dict(result[0]) is not None


def test_param_panel_nouvelles_actions(app):
    """Le panneau de paramètres se construit pour les nouvelles actions."""
    from autoflow.gui.param_panel import ParamPanel

    panel = ParamPanel()
    for type_name in ("for_each", "http_request", "send_email", "system_power",
                      "try_catch", "compound_condition", "user_input"):
        action = registry.create_action(type_name)
        panel.set_action(action)
        assert panel is not None
