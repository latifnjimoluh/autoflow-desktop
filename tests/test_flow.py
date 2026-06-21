"""Tests du contrôle de flux : conditions, boucles, sous-workflows, compat."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoflow.core import registry
from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow


def run_workflow(actions, inputs=None, windows=None, resolver=None):
    """Exécute une séquence via le vrai moteur et renvoie l'exécuteur."""
    inputs = inputs or MagicMock()
    windows = windows or MagicMock()
    wf = Workflow(name="Test", schedule=Schedule(mode="run_once"), actions=actions)
    executor = Executor(wf, inputs, windows, sleep_func=lambda _s: None,
                        workflow_resolver=resolver)
    executor.run()
    return executor


def sv(name, value):
    """Raccourci : action set_variable."""
    return registry.create_action("set_variable", params={"name": name, "value": value})


# -- Variables ------------------------------------------------------------
def test_set_and_increment_variable():
    actions = [
        sv("compteur", "0"),
        registry.create_action("increment_variable", params={"name": "compteur", "by": 2}),
        registry.create_action("increment_variable", params={"name": "compteur", "by": 3}),
    ]
    ex = run_workflow(actions)
    assert ex.variables.get("compteur") == 5


def test_substitution_dans_type_text():
    inputs = MagicMock()
    actions = [
        sv("nom", "Alice"),
        registry.create_action("type_text", params={"text": "Bonjour {{nom}} !"}),
    ]
    run_workflow(actions, inputs=inputs)
    inputs.type_text.assert_called_once_with("Bonjour Alice !", interval=0.0)


def test_variables_integrees_iteration():
    inputs = MagicMock()
    actions = [registry.create_action("type_text", params={"text": "it={{iteration}}"})]
    run_workflow(actions, inputs=inputs)
    inputs.type_text.assert_called_once_with("it=1", interval=0.0)


# -- Conditions -----------------------------------------------------------
def test_condition_branche_then():
    cond = registry.create_action("condition", params={
        "test": "variable_compare", "var_name": "x", "operator": ">", "value": "3"})
    cond.then_actions = [sv("res", "grand")]
    cond.else_actions = [sv("res", "petit")]
    ex = run_workflow([sv("x", "5"), cond])
    assert ex.variables.get("res") == "grand"


def test_condition_branche_else():
    cond = registry.create_action("condition", params={
        "test": "variable_compare", "var_name": "x", "operator": ">", "value": "3"})
    cond.then_actions = [sv("res", "grand")]
    cond.else_actions = [sv("res", "petit")]
    ex = run_workflow([sv("x", "1"), cond])
    assert ex.variables.get("res") == "petit"


def test_condition_fenetre_presente():
    windows = MagicMock()
    windows.find_windows.return_value = ["fenetre"]
    cond = registry.create_action("condition", params={
        "test": "window_present", "title": "Bloc-notes"})
    cond.then_actions = [sv("ok", "oui")]
    ex = run_workflow([cond], windows=windows)
    assert ex.variables.get("ok") == "oui"


# -- Boucles --------------------------------------------------------------
def test_loop_count():
    loop = registry.create_action("loop", params={"mode": "count", "count": 4})
    loop.body = [registry.create_action("increment_variable", params={"name": "n", "by": 1})]
    ex = run_workflow([sv("n", "0"), loop])
    assert ex.variables.get("n") == 4


def test_loop_while_respecte_condition():
    loop = registry.create_action("loop", params={
        "mode": "while", "test": "variable_compare",
        "var_name": "n", "operator": "<", "value": "3", "max_iterations": 100})
    loop.body = [registry.create_action("increment_variable", params={"name": "n", "by": 1})]
    ex = run_workflow([sv("n", "0"), loop])
    assert ex.variables.get("n") == 3


def test_loop_garde_fou_max():
    # Condition toujours vraie -> seul le garde-fou arrête la boucle.
    loop = registry.create_action("loop", params={
        "mode": "while", "test": "variable_compare",
        "var_name": "n", "operator": ">=", "value": "0", "max_iterations": 5})
    loop.body = [registry.create_action("increment_variable", params={"name": "n", "by": 1})]
    ex = run_workflow([sv("n", "0"), loop])
    assert ex.variables.get("n") == 5


def test_imbrication_condition_dans_boucle():
    inner = registry.create_action("condition", params={
        "test": "variable_compare", "var_name": "loop_index", "operator": "==", "value": "1"})
    inner.then_actions = [sv("touche", "oui")]
    loop = registry.create_action("loop", params={"mode": "count", "count": 3})
    loop.body = [inner]
    ex = run_workflow([loop])
    assert ex.variables.get("touche") == "oui"


# -- Sous-workflows -------------------------------------------------------
def test_run_workflow_appelle_le_sous_workflow():
    sub = Workflow(name="Sous", actions=[sv("appel", "fait")])
    resolver = lambda name: sub if name == "Sous" else None
    call = registry.create_action("run_workflow", params={"workflow_name": "Sous"})
    ex = run_workflow([call], resolver=resolver)
    assert ex.variables.get("appel") == "fait"


def test_run_workflow_introuvable_ne_plante_pas():
    call = registry.create_action("run_workflow", params={"workflow_name": "Absent"})
    ex = run_workflow([call], resolver=lambda _n: None)
    assert ex.iterations_done == 1  # le workflow s'est terminé proprement


def test_run_workflow_recursion_bloquee():
    # A appelle A : la récursion doit être détectée sans boucle infinie.
    a_actions = [registry.create_action("run_workflow", params={"workflow_name": "Test"})]
    wf = Workflow(name="Test", schedule=Schedule(mode="run_once"), actions=a_actions)
    inputs, windows = MagicMock(), MagicMock()
    resolver = lambda name: wf if name == "Test" else None
    executor = Executor(wf, inputs, windows, sleep_func=lambda _s: None,
                        workflow_resolver=resolver)
    # Ne doit pas boucler indéfiniment.
    assert executor.run() == 1


# -- Compatibilité ascendante --------------------------------------------
def test_ancien_workflow_plat_se_charge_et_execute():
    # Format « v1 » : pas de champs retries/on_error, pas d'imbrication.
    data = {
        "name": "Ancien",
        "description": "workflow plat hérité",
        "schedule": {"mode": "run_once"},
        "actions": [
            {"type": "type_text", "params": {"text": "salut"}, "enabled": True,
             "delay_after": 0.0},
            {"type": "key_press", "params": {"key": "enter"}, "enabled": True},
        ],
    }
    wf = Workflow.from_dict(data)
    assert len(wf.actions) == 2
    inputs = MagicMock()
    executor = Executor(wf, inputs, MagicMock(), sleep_func=lambda _s: None)
    executor.run()
    inputs.type_text.assert_called_once()
    inputs.press.assert_called_once()


def test_round_trip_condition_imbriquee():
    cond = registry.create_action("condition", params={"test": "window_present", "title": "X"})
    cond.then_actions = [sv("a", "1")]
    cond.else_actions = [registry.create_action("wait", params={"seconds": 2})]
    data = cond.to_dict()
    rebuilt = registry.action_from_dict(data)
    assert rebuilt.to_dict() == data
    assert len(rebuilt.then_actions) == 1
    assert len(rebuilt.else_actions) == 1
