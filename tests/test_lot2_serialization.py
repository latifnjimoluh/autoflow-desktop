"""Lot 2 — sérialisation des nouveaux types & **compatibilité ascendante**."""

from __future__ import annotations

from autoflow.core import registry
from autoflow.core.registry import action_from_dict
from autoflow.models.workflow import Workflow

NEW_ACTION_TYPES = [
    "for_each", "read_table", "write_table", "http_request", "text_transform",
    "math_eval", "set_global", "get_global", "get_secret", "file_operation",
    "read_file", "write_file", "send_email", "speak", "play_sound", "user_input",
    "system_power", "set_volume", "ui_element", "try_catch", "compound_condition",
]


def test_roundtrip_chaque_nouvelle_action():
    """Chaque nouvelle action se sérialise et se reconstruit à l'identique."""
    for type_name in NEW_ACTION_TYPES:
        action = registry.create_action(type_name)
        data = action.to_dict()
        clone = action_from_dict(data)
        assert clone.type_name == type_name
        assert clone.to_dict() == data


def test_roundtrip_structures_imbriquees():
    """Les conteneurs (for_each, try_catch, compound) conservent leurs enfants."""
    foreach = registry.create_action("for_each")
    foreach.body = [registry.create_action("wait", params={"seconds": 1})]

    trycatch = registry.create_action("try_catch")
    trycatch.try_actions = [registry.create_action("click")]
    trycatch.catch_actions = [registry.create_action("speak", params={"text": "oops"})]

    compound = registry.create_action("compound_condition", params={"logic": "OR"})
    compound.conditions = [{"test": "file_exists", "file_path": "x.txt"}]
    compound.then_actions = [registry.create_action("wait")]

    for action in (foreach, trycatch, compound):
        clone = action_from_dict(action.to_dict())
        assert clone.to_dict() == action.to_dict()
        assert clone.child_groups().keys() == action.child_groups().keys()

    assert action_from_dict(foreach.to_dict()).body[0].type_name == "wait"
    assert action_from_dict(trycatch.to_dict()).catch_actions[0].type_name == "speak"
    assert action_from_dict(compound.to_dict()).conditions[0]["test"] == "file_exists"


def test_workflow_avec_triggers_roundtrip():
    wf = Workflow(name="Réactif")
    wf.triggers = [{"type": "file_event", "params": {"folder": "/x", "pattern": "*.csv"},
                    "enabled": True}]
    wf.actions = [registry.create_action("read_table")]
    clone = Workflow.from_dict(wf.to_dict())
    assert clone.triggers == wf.triggers
    assert clone == wf


def test_compat_ancien_workflow_plat_sans_triggers():
    """Un ancien JOSN « plat » (sans clé triggers) se charge sans erreur."""
    ancien = {
        "name": "Ancien",
        "description": "workflow d'avant le lot 2",
        "schedule": {"mode": "loop_interval", "interval_seconds": 60},
        "actions": [
            {"type": "type_text", "params": {"text": "salut"}, "enabled": True,
             "delay_after": 0.0},
            {"type": "wait", "params": {"seconds": 1}},
        ],
    }
    wf = Workflow.from_dict(ancien)
    assert wf.name == "Ancien"
    assert wf.triggers == []           # par défaut, aucune régression
    assert len(wf.actions) == 2
    # Le re-sérialiser n'ajoute pas de clé « triggers » (compacité préservée).
    assert "triggers" not in wf.to_dict()


def test_compat_workflow_plat_executable():
    """L'ancien workflow plat s'exécute toujours correctement."""
    from unittest.mock import MagicMock

    from autoflow.core.executor import Executor
    ancien = {
        "name": "Plat",
        "schedule": {"mode": "run_once"},
        "actions": [{"type": "set_variable", "params": {"name": "x", "value": "ok"}}],
    }
    wf = Workflow.from_dict(ancien)
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=lambda _s: None)
    ex.run()
    assert ex.variables.get("x") == "ok"
