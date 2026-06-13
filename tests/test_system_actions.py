"""Tests des actions système : commande shell et presse-papiers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from autoflow.core import registry
from autoflow.core.actions import system
from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow


def run_workflow(actions, inputs=None):
    inputs = inputs or MagicMock()
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, inputs, MagicMock(), sleep_func=lambda _s: None)
    ex.run()
    return ex


def test_run_command_capture_sortie(monkeypatch):
    fake = SimpleNamespace(stdout="bonjour\n", stderr="", returncode=0)
    appels = {}

    def fake_run(cmd, **kwargs):
        appels["cmd"] = cmd
        appels["shell"] = kwargs.get("shell")
        return fake

    monkeypatch.setattr(system.subprocess, "run", fake_run)
    action = registry.create_action("run_command", params={
        "command": "echo bonjour", "output_var": "sortie"})
    ex = run_workflow([action])
    assert ex.variables.get("sortie") == "bonjour"
    assert ex.variables.get("sortie_code") == 0
    assert appels["cmd"] == "echo bonjour"


def test_run_command_substitue_variables(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(system.subprocess, "run", fake_run)
    sv = registry.create_action("set_variable", params={"name": "fichier", "value": "log.txt"})
    cmd = registry.create_action("run_command", params={"command": "type {{fichier}}"})
    run_workflow([sv, cmd])
    assert captured["cmd"] == "type log.txt"


def test_run_command_vide_invalide():
    action = registry.create_action("run_command", params={"command": ""})
    import pytest

    with pytest.raises(ValueError):
        action.validate()


def test_clipboard_set_then_get():
    sset = registry.create_action("clipboard_set", params={"text": "presse {{absent}}"})
    sget = registry.create_action("clipboard_get", params={"var_name": "lu"})
    ex = run_workflow([sset, sget])
    # Le texte écrit (gabarit non résolu car variable absente) est relu.
    assert ex.variables.get("lu") == "presse {{absent}}"


def test_clipboard_paste_envoie_ctrl_v():
    inputs = MagicMock()
    action = registry.create_action("clipboard_paste", params={"text": "coller"})
    run_workflow([action], inputs=inputs)
    inputs.hotkey.assert_called_once_with(["ctrl", "v"])
