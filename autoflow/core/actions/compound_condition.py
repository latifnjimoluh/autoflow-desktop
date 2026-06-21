"""Condition **composée** (ET / OU) : combine plusieurs tests avec une logique.

Contrairement à la condition simple, celle-ci évalue une **liste** de tests reliés
par ``ET`` (tous vrais) ou ``OU`` (au moins un vrai), puis exécute la branche
*alors* ou *sinon*. La liste de tests est sérialisée dans le workflow (clé
``conditions``) : compatible avec le format existant.
"""

from __future__ import annotations

from typing import Any

from .. import conditions
from ..registry import action_from_dict, register
from .base import Action, ParamSpec


@register
class CompoundConditionAction(Action):
    """Si (tests reliés par ET/OU) alors … sinon …."""

    type_name = "compound_condition"
    label = "Condition composée (ET / OU)"
    category = "Contrôle"

    def __init__(self, *args: Any, conditions_list=None, then_actions=None,
                 else_actions=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.conditions: list[dict[str, Any]] = list(conditions_list or [])
        self.then_actions: list[Action] = list(then_actions or [])
        self.else_actions: list[Action] = list(else_actions or [])

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("logic", "Logique entre les tests", "choice", "AND",
                      choices=["AND", "OR"],
                      help="ET : tous les tests vrais. OU : au moins un test vrai."),
        ]

    def child_groups(self) -> dict[str, list[Action]]:
        return {"alors": self.then_actions, "sinon": self.else_actions}

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        logic = str(self.params.get("logic", "AND"))
        result = conditions.evaluate_all(self.conditions, logic, inputs, windows, context)
        log = (context or {}).get("log")
        if callable(log):
            log(f"Condition composée ({logic}, {len(self.conditions)} test(s)) = {result}",
                "info")
        runner = (context or {}).get("run_actions")
        if callable(runner):
            runner(self.then_actions if result else self.else_actions)
        return result

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["conditions"] = [dict(c) for c in self.conditions]
        data["then"] = [a.to_dict() for a in self.then_actions]
        data["else"] = [a.to_dict() for a in self.else_actions]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompoundConditionAction:
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
            conditions_list=[dict(c) for c in data.get("conditions", [])],
            then_actions=[action_from_dict(d) for d in data.get("then", [])],
            else_actions=[action_from_dict(d) for d in data.get("else", [])],
        )

    def summary(self) -> str:
        logic = "ET" if self.params.get("logic", "AND") == "AND" else "OU"
        return (f"Si ({len(self.conditions)} test(s) reliés par {logic}) : "
                f"{len(self.then_actions)} sinon {len(self.else_actions)}")
