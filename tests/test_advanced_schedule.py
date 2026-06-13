"""Tests de la planification avancée (cron / jours / horaires)."""

from __future__ import annotations

from datetime import datetime

from autoflow.core import advanced_schedule as adv
from autoflow.models.workflow import Schedule


def test_validate_cron():
    assert adv.validate_cron("0 9 * * *") is True
    assert adv.validate_cron("pas du cron") is False


def test_next_run_times_cron_quotidien():
    sched = Schedule(mode="cron", cron="0 9 * * *")
    now = datetime(2026, 1, 1, 8, 0, 0)
    echeances = adv.next_run_times(sched, count=2, now=now)
    assert len(echeances) == 2
    assert echeances[0] == datetime(2026, 1, 1, 9, 0, 0)
    assert echeances[1] == datetime(2026, 1, 2, 9, 0, 0)


def test_next_run_times_horaires_multiples():
    sched = Schedule(mode="cron", times=["09:00", "18:00"])
    now = datetime(2026, 1, 1, 8, 0, 0)
    echeances = adv.next_run_times(sched, count=2, now=now)
    assert echeances[0].hour == 9
    assert echeances[1].hour == 18


def test_next_run_times_jours_de_semaine():
    sched = Schedule(mode="cron", days=["mon"], times=["09:00"])
    now = datetime(2026, 1, 1, 8, 0, 0)  # 2026-01-01 est un jeudi
    echeances = adv.next_run_times(sched, count=1, now=now)
    # La prochaine occurrence doit tomber un lundi.
    assert echeances[0].weekday() == 0


def test_schedule_manager_planifie_et_retire():
    manager = adv.ScheduleManager()
    appels = []
    sched = Schedule(mode="cron", cron="0 9 * * *")
    manager.schedule_workflow("WF", sched, lambda: appels.append(1))
    assert "WF" in manager.active()
    manager.remove("WF")
    assert "WF" not in manager.active()
    manager.shutdown()
