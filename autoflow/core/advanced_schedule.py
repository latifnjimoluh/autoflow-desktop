"""Planification avancée : cron, jours de la semaine, horaires multiples.

S'appuie sur **APScheduler** (en mémoire, sans serveur). Fournit aussi des
fonctions pures (calcul des prochaines échéances, validation cron) testables
sans attente réelle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models.workflow import Schedule

# Jours acceptés (abréviations APScheduler).
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def build_trigger(schedule: Schedule) -> Any:
    """Construit un trigger APScheduler à partir d'un :class:`Schedule`.

    Priorité : expression cron explicite, sinon jours + horaires.
    """
    from apscheduler.triggers.cron import CronTrigger

    if schedule.cron.strip():
        return CronTrigger.from_crontab(schedule.cron.strip())

    day_of_week = ",".join(schedule.days) if schedule.days else None
    times = schedule.times or [schedule.at_time]
    hours = sorted({t.split(":")[0] for t in times})
    minutes = sorted({t.split(":")[1] for t in times})
    return CronTrigger(
        day_of_week=day_of_week,
        hour=",".join(hours),
        minute=",".join(minutes),
    )


def validate_cron(expression: str) -> bool:
    """Indique si une expression cron (5 champs) est valide."""
    try:
        from apscheduler.triggers.cron import CronTrigger

        CronTrigger.from_crontab(expression.strip())
        return True
    except Exception:  # noqa: BLE001
        return False


def next_run_times(schedule: Schedule, count: int = 3,
                   now: datetime | None = None) -> list[datetime]:
    """Renvoie les ``count`` prochaines échéances du planning."""
    trigger = build_trigger(schedule)
    now = now or datetime.now()
    results: list[datetime] = []
    previous = None
    current = now
    for _ in range(count):
        nxt = trigger.get_next_fire_time(previous, current)
        if nxt is None:
            break
        # APScheduler renvoie un datetime éventuellement « aware ».
        nxt_naive = nxt.replace(tzinfo=None)
        results.append(nxt_naive)
        previous = nxt
        current = nxt
    return results


class ScheduleManager:
    """Enregistre les workflows à planification avancée dans un BackgroundScheduler."""

    def __init__(self) -> None:
        self._scheduler = None
        self.jobs: dict[str, Any] = {}

    def start(self) -> None:
        """Démarre le planificateur de fond."""
        from apscheduler.schedulers.background import BackgroundScheduler

        if self._scheduler is None:
            self._scheduler = BackgroundScheduler()
            self._scheduler.start()

    def schedule_workflow(self, name: str, schedule: Schedule, callback) -> None:
        """Planifie l'exécution d'un workflow selon son planning avancé."""
        self.start()
        if name in self.jobs:
            self.remove(name)
        job = self._scheduler.add_job(callback, build_trigger(schedule), id=name,
                                      replace_existing=True)
        self.jobs[name] = job

    def remove(self, name: str) -> None:
        """Retire un workflow planifié."""
        if self._scheduler is not None and name in self.jobs:
            try:
                self._scheduler.remove_job(name)
            except Exception:  # noqa: BLE001
                pass
            self.jobs.pop(name, None)

    def active(self) -> list[str]:
        """Renvoie les noms des workflows actuellement planifiés."""
        return list(self.jobs)

    def shutdown(self) -> None:
        """Arrête le planificateur."""
        if self._scheduler is not None:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:  # noqa: BLE001
                pass
            self._scheduler = None
            self.jobs.clear()
