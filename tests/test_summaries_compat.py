"""Tests des résumés en langage naturel + compatibilité ascendante v3."""

from __future__ import annotations

from unittest.mock import MagicMock

import autoflow.core.actions  # noqa: F401 - peuple le registre
from autoflow.core import registry
from autoflow.core.actions.base import ParamSpec
from autoflow.core.executor import Executor
from autoflow.models.workflow import Workflow


# -- Résumés en langage naturel -------------------------------------------
def test_chaque_action_a_un_resume_lisible():
    for type_name, _label in registry.available_types():
        action = registry.create_action(type_name)
        resume = action.summary()
        assert isinstance(resume, str) and resume.strip()


def test_resumes_specifiques_naturels():
    click = registry.create_action("click", params={"x": 120, "y": 340, "button": "left"})
    assert click.summary() == "Clic gauche à la position (120, 340)"

    key = registry.create_action("key_press", params={"key": "enter", "presses": 3})
    assert "Entrée" in key.summary() and "3 fois" in key.summary()

    hot = registry.create_action("hotkey", params={"keys": ["ctrl", "s"]})
    assert hot.summary() == "Raccourci clavier « Ctrl + S »"

    win = registry.create_action("activate_window", params={"title": "Chrome"})
    assert "Chrome" in win.summary()


# -- Nouveaux champs de ParamSpec (rétro-compatibles) ---------------------
def test_paramspec_nouveaux_champs_par_defaut():
    spec = ParamSpec("x", "X")  # ancienne signature minimale
    assert spec.placeholder == ""
    assert spec.supports_vars is False
    assert spec.depends_on is None


def test_paramspec_supporte_les_nouveaux_champs():
    spec = ParamSpec("text", "Texte", "text", supports_vars=True,
                     placeholder="Ex", depends_on=("paste", False))
    assert spec.supports_vars is True
    assert spec.depends_on == ("paste", False)


# -- Compatibilité ascendante : ancien workflow « plat » ------------------
_OLD_FLAT_WORKFLOW = {
    "name": "Ancien workflow plat",
    "description": "Format historique sans imbrication ni champs de politique.",
    "schedule": {"mode": "loop_interval", "interval_seconds": 60, "max_iterations": 2},
    "actions": [
        {"type": "activate_window",
         "params": {"title": "Bloc-notes", "match": "contains", "force_foreground": False},
         "enabled": True, "delay_after": 0.3},
        {"type": "hotkey", "params": {"keys": ["ctrl", "end"]},
         "enabled": True, "delay_after": 0.1},
        {"type": "type_text", "params": {"text": ".", "interval": 0.05},
         "enabled": True, "delay_after": 0.0},
    ],
}


def test_ancien_workflow_se_charge():
    wf = Workflow.from_dict(_OLD_FLAT_WORKFLOW)
    assert wf.name == "Ancien workflow plat"
    assert len(wf.actions) == 3
    # Le type_text historique (sans 'paste') reste valide.
    assert wf.actions[2].type_name == "type_text"


def test_ancien_workflow_s_execute():
    wf = Workflow.from_dict(_OLD_FLAT_WORKFLOW)
    inputs = MagicMock()
    windows = MagicMock()
    windows.activate.return_value = True
    executor = Executor(wf, inputs, windows, sleep_func=lambda _s: None)
    iterations = executor.run()
    assert iterations == 2  # max_iterations respecté
    # Les actions ont bien été déléguées aux backends mockés.
    assert windows.activate.called
    assert inputs.hotkey.called
    assert inputs.type_text.called


def test_type_text_historique_sans_paste_tape_normalement():
    """Un type_text sans le nouveau champ 'paste' doit taper (pas coller)."""
    action = registry.create_action("type_text", params={"text": "abc", "interval": 0.0})
    inputs = MagicMock()
    action.execute(inputs, MagicMock(), {})
    inputs.type_text.assert_called_once()
