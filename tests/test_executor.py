"""Tests du moteur d'exécution."""

from __future__ import annotations

import threading

import pytest

from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow


class FakeAction:
    """Action factice enregistrant ses exécutions (sans toucher au matériel)."""

    def __init__(self, name, enabled=True, delay_after=0.0, on_execute=None, boom=False):
        self.name = name
        self.type_name = name
        self.enabled = enabled
        self.delay_after = delay_after
        self._on_execute = on_execute
        self._boom = boom

    def summary(self):
        return self.name

    def execute(self, inputs, windows, context):
        if self._on_execute:
            self._on_execute(self)
        if self._boom:
            raise RuntimeError("échec simulé")


def make_executor(actions, schedule=None, **kwargs):
    workflow = Workflow(name="Test", schedule=schedule or Schedule(mode="run_once"),
                        actions=actions)
    sleeps = []
    executor = Executor(
        workflow,
        inputs=object(),
        windows=object(),
        sleep_func=sleeps.append,
        **kwargs,
    )
    return executor, sleeps


def test_execute_dans_l_ordre():
    order = []
    actions = [FakeAction(f"a{i}", on_execute=lambda a: order.append(a.name)) for i in range(3)]
    executor, _ = make_executor(actions)
    executor.run()
    assert order == ["a0", "a1", "a2"]


def test_ignore_actions_desactivees():
    order = []
    actions = [
        FakeAction("a0", on_execute=lambda a: order.append(a.name)),
        FakeAction("a1", enabled=False, on_execute=lambda a: order.append(a.name)),
        FakeAction("a2", on_execute=lambda a: order.append(a.name)),
    ]
    executor, _ = make_executor(actions)
    executor.run()
    assert order == ["a0", "a2"]


def test_respecte_delay_after():
    actions = [FakeAction("a0", delay_after=1.5), FakeAction("a1", delay_after=2.0)]
    executor, sleeps = make_executor(actions)
    executor.run()
    assert 1.5 in sleeps and 2.0 in sleeps


def test_arret_en_plein_milieu():
    order = []

    def stopper(action):
        order.append(action.name)
        if action.name == "a1":
            executor.request_stop()

    actions = [FakeAction(f"a{i}", on_execute=stopper) for i in range(4)]
    executor, _ = make_executor(actions)
    executor.run()
    # a2 et a3 ne doivent pas s'exécuter après l'arrêt demandé sur a1.
    assert order == ["a0", "a1"]


def test_exception_continue_par_defaut():
    order = []
    actions = [
        FakeAction("a0", on_execute=lambda a: order.append(a.name)),
        FakeAction("a1", boom=True, on_execute=lambda a: order.append(a.name)),
        FakeAction("a2", on_execute=lambda a: order.append(a.name)),
    ]
    logs = []
    executor, _ = make_executor(actions, log=lambda m, l="info": logs.append((m, l)))
    executor.run()
    assert order == ["a0", "a1", "a2"]
    assert any(level == "error" for _m, level in logs)


def test_exception_stoppe_si_demande():
    order = []
    actions = [
        FakeAction("a0", on_execute=lambda a: order.append(a.name)),
        FakeAction("a1", boom=True, on_execute=lambda a: order.append(a.name)),
        FakeAction("a2", on_execute=lambda a: order.append(a.name)),
    ]
    executor, _ = make_executor(actions, continue_on_error=False)
    executor.run()
    assert order == ["a0", "a1"]


def test_repeat_n_repete_le_workflow():
    count = []
    actions = [FakeAction("a0", on_execute=lambda a: count.append(1))]
    schedule = Schedule(mode="repeat_n", max_iterations=3)
    executor, _ = make_executor(actions, schedule=schedule)
    iterations = executor.run()
    assert iterations == 3
    assert len(count) == 3


def test_loop_interval_avec_max_et_delai():
    count = []
    actions = [FakeAction("a0", on_execute=lambda a: count.append(1))]
    schedule = Schedule(mode="loop_interval", interval_seconds=10, max_iterations=2)
    executor, sleeps = make_executor(actions, schedule=schedule)
    iterations = executor.run()
    assert iterations == 2
    assert len(count) == 2
    # Un seul délai entre les deux itérations (pas après la dernière).
    assert sleeps.count(10) == 1


def test_failsafe_provoque_arret():
    class FailSafeException(Exception):
        pass

    def boom(_a):
        raise FailSafeException("coin haut-gauche")

    order = []
    actions = [
        FakeAction("a0", on_execute=lambda a: order.append("a0")),
        FakeAction("a1", on_execute=boom),
        FakeAction("a2", on_execute=lambda a: order.append("a2")),
    ]
    executor, _ = make_executor(actions)
    executor.run()
    assert order == ["a0"]


def test_statut_emis():
    statuses = []
    actions = [FakeAction("a0")]
    executor, _ = make_executor(actions, on_status=statuses.append)
    executor.run()
    assert statuses[0] == "running"
    assert statuses[-1] == "stopped"


def test_pause_puis_reprise_dans_un_thread():
    a0_done = threading.Event()
    a1_done = threading.Event()

    def on_exec(action):
        if action.name == "a0":
            # La première action déclenche la pause : la seconde devra
            # attendre la reprise avant de s'exécuter.
            executor.pause()
            a0_done.set()
        elif action.name == "a1":
            a1_done.set()

    actions = [FakeAction("a0", on_execute=on_exec), FakeAction("a1", on_execute=on_exec)]
    workflow = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    executor = Executor(workflow, object(), object())
    thread = threading.Thread(target=executor.run)
    thread.start()

    assert a0_done.wait(timeout=1.0)
    # a1 ne doit pas s'exécuter tant que l'on n'a pas repris.
    assert not a1_done.wait(timeout=0.2)
    assert executor.is_paused()
    executor.resume()
    assert a1_done.wait(timeout=1.0)
    thread.join(timeout=2.0)
    assert not thread.is_alive()
