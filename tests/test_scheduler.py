"""Tests de la logique de planification."""

from __future__ import annotations

from datetime import datetime

import pytest

from autoflow.core.scheduler import Scheduler, seconds_until_time
from autoflow.models.workflow import Schedule


def test_run_once_une_seule_iteration():
    sched = Scheduler(Schedule(mode="run_once"))
    assert sched.total_iterations() == 1
    assert sched.should_run(0) is True
    assert sched.should_run(1) is False
    assert sched.is_infinite is False


def test_loop_interval_infini():
    sched = Scheduler(Schedule(mode="loop_interval", max_iterations=0))
    assert sched.total_iterations() is None
    assert sched.is_infinite is True
    assert sched.should_run(10_000) is True


def test_loop_interval_borne():
    sched = Scheduler(Schedule(mode="loop_interval", interval_seconds=30, max_iterations=5))
    assert sched.total_iterations() == 5
    assert sched.should_run(4) is True
    assert sched.should_run(5) is False
    assert sched.delay_after_iteration() == 30


def test_repeat_n():
    sched = Scheduler(Schedule(mode="repeat_n", max_iterations=3))
    assert sched.total_iterations() == 3
    assert sched.delay_after_iteration() == 0


def test_repeat_n_minimum_un():
    sched = Scheduler(Schedule(mode="repeat_n", max_iterations=0))
    assert sched.total_iterations() == 1


def test_seconds_until_time_futur():
    now = datetime(2026, 1, 1, 8, 0, 0)
    assert seconds_until_time("08:30", now) == 30 * 60


def test_seconds_until_time_lendemain():
    now = datetime(2026, 1, 1, 9, 0, 0)
    # 08:00 est passé → vise le lendemain.
    assert seconds_until_time("08:00", now) == 23 * 3600


def test_seconds_until_time_invalide():
    with pytest.raises(ValueError):
        seconds_until_time("pasunheure", datetime.now())


def test_initial_delay_seulement_at_time():
    now = datetime(2026, 1, 1, 8, 0, 0)
    assert Scheduler(Schedule(mode="run_once")).initial_delay(now) == 0.0
    assert Scheduler(Schedule(mode="at_time", at_time="08:10")).initial_delay(now) == 600
