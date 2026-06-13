"""Dataclasses décrivant un workflow, son planning et ses actions.

Le modèle s'appuie sur le registre pour (dé)sérialiser les actions, ce qui
préserve l'extensibilité : un nouveau type d'action est pris en charge sans
modifier ce module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.actions.base import Action
from ..core.registry import action_from_dict

# Modes de planification reconnus.
SCHEDULE_MODES = (
    "run_once",
    "loop_interval",
    "repeat_n",
    "at_time",
    "hotkey_trigger",
    "cron",
)


@dataclass
class Schedule:
    """Planning d'un workflow.

    Attributs :
        mode : un des :data:`SCHEDULE_MODES`.
        interval_seconds : pause entre itérations (mode ``loop_interval``).
        max_iterations : nombre d'itérations ; ``0`` signifie infini.
        at_time : heure de déclenchement « HH:MM » (mode ``at_time``).
        hotkey : raccourci global déclencheur (mode ``hotkey_trigger``).
    """

    mode: str = "run_once"
    interval_seconds: float = 900.0
    max_iterations: int = 0
    at_time: str = "08:00"
    hotkey: str = "ctrl+shift+r"
    cron: str = ""
    days: list[str] = field(default_factory=list)
    times: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in SCHEDULE_MODES:
            raise ValueError(f"Mode de planning inconnu : {self.mode!r}.")

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le planning."""
        return {
            "mode": self.mode,
            "interval_seconds": self.interval_seconds,
            "max_iterations": self.max_iterations,
            "at_time": self.at_time,
            "hotkey": self.hotkey,
            "cron": self.cron,
            "days": list(self.days),
            "times": list(self.times),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Schedule":
        """Reconstruit un planning depuis un dictionnaire (tolère l'absence)."""
        data = data or {}
        return cls(
            mode=data.get("mode", "run_once"),
            interval_seconds=float(data.get("interval_seconds", 900.0)),
            max_iterations=int(data.get("max_iterations", 0)),
            at_time=str(data.get("at_time", "08:00")),
            hotkey=str(data.get("hotkey", "ctrl+shift+r")),
            cron=str(data.get("cron", "")),
            days=list(data.get("days", [])),
            times=list(data.get("times", [])),
        )


@dataclass
class Workflow:
    """Séquence nommée d'actions, dotée d'un planning."""

    name: str = "Nouveau workflow"
    description: str = ""
    schedule: Schedule = field(default_factory=Schedule)
    actions: list[Action] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le workflow complet en dictionnaire JSON-compatible."""
        return {
            "name": self.name,
            "description": self.description,
            "schedule": self.schedule.to_dict(),
            "actions": [action.to_dict() for action in self.actions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        """Reconstruit un workflow depuis un dictionnaire."""
        return cls(
            name=str(data.get("name", "Nouveau workflow")),
            description=str(data.get("description", "")),
            schedule=Schedule.from_dict(data.get("schedule")),
            actions=[action_from_dict(a) for a in data.get("actions", [])],
        )

    def enabled_actions(self) -> list[Action]:
        """Renvoie uniquement les actions activées (dans l'ordre)."""
        return [a for a in self.actions if a.enabled]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workflow):
            return NotImplemented
        return self.to_dict() == other.to_dict()
