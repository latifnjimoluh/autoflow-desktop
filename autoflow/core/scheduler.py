"""Logique de planification et de déclenchement des workflows.

Fonctions pures (testables sans horloge réelle) calculant, selon le planning,
le nombre d'itérations et les délais entre elles.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..models.workflow import Schedule


class Scheduler:
    """Encapsule un :class:`Schedule` et en dérive le plan d'exécution."""

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

    @property
    def is_infinite(self) -> bool:
        """Vrai si le workflow doit boucler indéfiniment."""
        return self.schedule.mode == "loop_interval" and self.schedule.max_iterations <= 0

    def total_iterations(self) -> int | None:
        """Nombre total d'itérations prévues (``None`` = infini)."""
        mode = self.schedule.mode
        if mode in ("run_once", "at_time", "hotkey_trigger", "cron"):
            return 1
        if mode == "repeat_n":
            return max(1, int(self.schedule.max_iterations or 1))
        if mode == "loop_interval":
            if self.schedule.max_iterations <= 0:
                return None
            return int(self.schedule.max_iterations)
        return 1

    def should_run(self, iterations_done: int) -> bool:
        """Indique si une nouvelle itération doit avoir lieu."""
        total = self.total_iterations()
        if total is None:
            return True
        return iterations_done < total

    def delay_after_iteration(self) -> float:
        """Délai (s) à observer après une itération, avant la suivante."""
        if self.schedule.mode == "loop_interval":
            return max(0.0, float(self.schedule.interval_seconds))
        # ``repeat_n`` enchaîne les itérations sans attente entre elles.
        return 0.0

    def initial_delay(self, now: datetime | None = None) -> float:
        """Délai initial (s) avant la première exécution (mode ``at_time``)."""
        if self.schedule.mode != "at_time":
            return 0.0
        now = now or datetime.now()
        return seconds_until_time(self.schedule.at_time, now)


def seconds_until_time(at_time: str, now: datetime) -> float:
    """Renvoie le nombre de secondes jusqu'à la prochaine occurrence de « HH:MM ».

    Si l'heure est déjà passée aujourd'hui, vise le lendemain.
    """
    try:
        hour, minute = (int(part) for part in at_time.split(":"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Heure invalide : {at_time!r} (attendu « HH:MM »).") from exc
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()
