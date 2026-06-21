"""Bloc **try / en cas d'erreur** : exécute une séquence et, en cas d'échec,
bascule sur une séquence de récupération. Va au-delà du retry par action.
"""

from __future__ import annotations

from typing import Any

from ..registry import action_from_dict, register
from .base import Action, ParamSpec


@register
class TryCatchAction(Action):
    """Essaie un groupe d'actions ; si l'une échoue, exécute la branche d'erreur."""

    type_name = "try_catch"
    label = "Essayer / en cas d'erreur"
    category = "Contrôle"

    def __init__(self, *args: Any, try_actions=None, catch_actions=None,
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.try_actions: list[Action] = list(try_actions or [])
        self.catch_actions: list[Action] = list(catch_actions or [])

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("error_var", "Stocker le message d'erreur dans", "variable",
                      "erreur", help="Variable contenant le message en cas d'échec."),
        ]

    def child_groups(self) -> dict[str, list[Action]]:
        return {"essayer": self.try_actions, "en cas d'erreur": self.catch_actions}

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        runner = (context or {}).get("run_actions_catching")
        plain = (context or {}).get("run_actions")
        log = (context or {}).get("log")
        error: Exception | None = None
        if callable(runner):
            error = runner(self.try_actions)
        elif callable(plain):
            plain(self.try_actions)  # repli : pas d'interception disponible

        if error is None:
            return True

        store = (context or {}).get("variables")
        var = str(self.params.get("error_var", "")).strip()
        if store is not None and var:
            store.set(var, str(error))
        if callable(log):
            log(f"Bloc « essayer » échoué ({error}) : exécution de la branche "
                f"d'erreur.", "warning")
        if callable(plain):
            plain(self.catch_actions)
        return False

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["try"] = [a.to_dict() for a in self.try_actions]
        data["catch"] = [a.to_dict() for a in self.catch_actions]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TryCatchAction:
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
            try_actions=[action_from_dict(d) for d in data.get("try", [])],
            catch_actions=[action_from_dict(d) for d in data.get("catch", [])],
        )

    def summary(self) -> str:
        return (f"Essayer {len(self.try_actions)} action(s), "
                f"sinon {len(self.catch_actions)}")
