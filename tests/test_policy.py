"""Tests de la politique par action : ré-essais et comportement en cas d'échec."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow


class ScriptedAction:
    """Action factice échouant un nombre de fois donné avant de réussir."""

    def __init__(self, name, fail_times=0, retries=0, retry_delay=0.0,
                 on_error="inherit", record=None):
        self.name = name
        self.type_name = name
        self.enabled = True
        self.delay_after = 0.0
        self.delay_jitter = 0.0
        self.retries = retries
        self.retry_delay = retry_delay
        self.on_error = on_error
        self._fail_times = fail_times
        self._record = record
        self.calls = 0

    def summary(self):
        return self.name

    def execute(self, inputs, windows, context):
        self.calls += 1
        if self._record is not None:
            self._record.append(self.name)
        if self.calls <= self._fail_times:
            raise RuntimeError("échec simulé")


def run(actions, continue_on_error=True):
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=lambda _s: None,
                  continue_on_error=continue_on_error)
    ex.run()
    return ex


def test_retry_reussit_apres_essais():
    action = ScriptedAction("a", fail_times=2, retries=3)
    run([action])
    assert action.calls == 3  # 2 échecs + 1 succès


def test_retry_epuise_puis_continue():
    order = []
    a = ScriptedAction("a", fail_times=5, retries=1, on_error="continue", record=order)
    b = ScriptedAction("b", record=order)
    run([a, b])
    assert a.calls == 2  # 1 essai + 1 retry
    assert "b" in order  # l'exécution continue malgré l'échec


def test_on_error_stop_arrete_le_workflow():
    order = []
    a = ScriptedAction("a", fail_times=5, retries=0, on_error="stop", record=order)
    b = ScriptedAction("b", record=order)
    run([a, b])
    assert "b" not in order  # b ne s'exécute pas après l'arrêt


def test_on_error_inherit_suit_continue_on_error():
    order = []
    a = ScriptedAction("a", fail_times=5, on_error="inherit", record=order)
    b = ScriptedAction("b", record=order)
    run([a, b], continue_on_error=False)
    assert "b" not in order


def test_jitter_ajoute_un_delai(monkeypatch):
    import random

    rng = random.Random(0)
    sleeps = []
    action = ScriptedAction("a")
    action.delay_after = 1.0
    action.delay_jitter = 0.5
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=[action])
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=sleeps.append, rng=rng)
    ex.run()
    # Le délai effectif est compris entre delay_after et delay_after + jitter.
    assert any(1.0 <= s <= 1.5 for s in sleeps)
