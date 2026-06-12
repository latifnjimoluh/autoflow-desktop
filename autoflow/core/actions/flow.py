"""Actions de contrôle de flux : condition, boucle, sous-workflow.

Ces actions contiennent des sous-séquences d'actions (« enfants ») et s'appuient
sur ``context["run_actions"]`` fourni par le moteur pour les exécuter. Leur
sérialisation étend le format JSON tout en restant lisible.
"""

from __future__ import annotations

from typing import Any

from .. import conditions
from ..registry import action_from_dict, register
from .base import Action, ParamSpec

# Champs de paramètres décrivant un test (réutilisés par condition et boucle).
# Chaque champ n'apparaît que pour le(s) type(s) de test concerné(s) grâce à
# ``depends_on`` : l'utilisateur ne voit que les réglages pertinents.
_CONDITION_SPECS = [
    ParamSpec("test", "Type de test", "choice", "window_present",
              choices=list(conditions.CONDITION_TESTS.keys()),
              help="Choisissez ce qui doit être vérifié ; les champs s'adaptent."),
    ParamSpec("title", "Fenêtre", "window", "",
              placeholder="Ex : Chrome",
              depends_on=("test", ("window_present", "window_absent"))),
    ParamSpec("match", "Correspondance du titre", "choice", "contains",
              choices=["contains", "exact"],
              depends_on=("test", ("window_present", "window_absent"))),
    ParamSpec("image_path", "Image à détecter", "file", "",
              depends_on=("test", "image_present")),
    ParamSpec("confidence", "Confiance (0-1)", "float", 0.8,
              depends_on=("test", "image_present")),
    ParamSpec("x", "X", "int", 0, depends_on=("test", "pixel_color")),
    ParamSpec("y", "Y", "int", 0, depends_on=("test", "pixel_color")),
    ParamSpec("color", "Couleur attendue", "color", "#000000",
              depends_on=("test", "pixel_color")),
    ParamSpec("tolerance", "Tolérance", "int", 10,
              depends_on=("test", "pixel_color")),
    ParamSpec("file_path", "Fichier", "file", "",
              depends_on=("test", "file_exists")),
    ParamSpec("var_name", "Variable", "variable", "",
              depends_on=("test", "variable_compare")),
    ParamSpec("operator", "Opérateur", "choice", "==",
              choices=["==", "!=", ">", "<", ">=", "<=", "contains"],
              depends_on=("test", "variable_compare")),
    ParamSpec("value", "Valeur à comparer", "str", "", supports_vars=True,
              depends_on=("test", "variable_compare")),
]


@register
class ConditionAction(Action):
    """Exécute la branche « alors » ou « sinon » selon un test."""

    type_name = "condition"
    label = "Condition (si / sinon)"
    category = "Contrôle"

    def __init__(self, *args: Any, then_actions=None, else_actions=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.then_actions: list[Action] = list(then_actions or [])
        self.else_actions: list[Action] = list(else_actions or [])

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return list(_CONDITION_SPECS)

    def child_groups(self) -> dict[str, list[Action]]:
        return {"alors": self.then_actions, "sinon": self.else_actions}

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        result = conditions.evaluate(self.params, inputs, windows, context)
        branche = self.then_actions if result else self.else_actions
        log = (context or {}).get("log")
        if callable(log):
            log(f"Condition « {self._test_label()} » = {result}", "info")
        runner = (context or {}).get("run_actions")
        if callable(runner):
            runner(branche)
        return result

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["then"] = [a.to_dict() for a in self.then_actions]
        data["else"] = [a.to_dict() for a in self.else_actions]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConditionAction":
        action = cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
            then_actions=[action_from_dict(d) for d in data.get("then", [])],
            else_actions=[action_from_dict(d) for d in data.get("else", [])],
        )
        return action

    def _test_label(self) -> str:
        return conditions.CONDITION_TESTS.get(self.params.get("test", ""),
                                              self.params.get("test", ""))

    def summary(self) -> str:
        return (f"Si « {self._test_label()} » : {len(self.then_actions)} action(s), "
                f"sinon {len(self.else_actions)}")


@register
class LoopAction(Action):
    """Répète un corps d'actions : N fois, tant que, ou jusqu'à une condition."""

    type_name = "loop"
    label = "Boucle / bloc répété"
    category = "Contrôle"

    def __init__(self, *args: Any, body=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.body: list[Action] = list(body or [])

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        specs = [
            ParamSpec("mode", "Type de boucle", "choice", "count",
                      choices=["count", "while", "until"],
                      help="N fois, tant que (while) ou jusqu'à (until) une condition."),
            ParamSpec("count", "Nombre de répétitions", "int", 3,
                      depends_on=("mode", "count")),
            ParamSpec("max_iterations", "Garde-fou : itérations max", "int", 1000,
                      help="Sécurité contre les boucles infinies."),
        ]
        # En mode while/until, on réutilise les champs de condition (sans la
        # ligne « count » déjà gérée ci-dessus).
        return specs + list(_CONDITION_SPECS)

    def child_groups(self) -> dict[str, list[Action]]:
        return {"corps": self.body}

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        mode = self.params.get("mode", "count")
        guard = int(self.params.get("max_iterations", 1000) or 1000)
        runner = (context or {}).get("run_actions")
        store = (context or {}).get("variables")
        i = 0
        while i < guard:
            if mode == "count":
                if i >= int(self.params.get("count", 0) or 0):
                    break
            elif mode == "while":
                if not conditions.evaluate(self.params, inputs, windows, context):
                    break
            elif mode == "until":
                if conditions.evaluate(self.params, inputs, windows, context):
                    break
            else:
                raise ValueError(f"Mode de boucle inconnu : {mode!r}")
            if store is not None:
                store.set("loop_index", i)
            if callable(runner):
                runner(self.body)
            i += 1
        if i >= guard:
            log = (context or {}).get("log")
            if callable(log):
                log(f"Boucle arrêtée par le garde-fou ({guard} itérations).", "warning")
        return i

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["body"] = [a.to_dict() for a in self.body]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoopAction":
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
            body=[action_from_dict(d) for d in data.get("body", [])],
        )

    def summary(self) -> str:
        mode = self.params.get("mode", "count")
        if mode == "count":
            return f"Boucle ×{self.params.get('count')} ({len(self.body)} action(s))"
        return f"Boucle {mode} ({len(self.body)} action(s))"


@register
class RunWorkflowAction(Action):
    """Exécute un autre workflow enregistré (brique réutilisable)."""

    type_name = "run_workflow"
    label = "Exécuter un sous-workflow"
    category = "Contrôle"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [ParamSpec("workflow_name", "Workflow à exécuter", "workflow", "",
                          help="Choisissez un workflow existant à réutiliser.")]

    def validate(self) -> None:
        if not str(self.params.get("workflow_name", "")).strip():
            raise ValueError("Le nom du sous-workflow ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        name = str(self.params["workflow_name"]).strip()
        resolver = (context or {}).get("workflow_resolver")
        log = (context or {}).get("log")
        call_stack = (context or {}).get("call_stack", [])
        if name in call_stack:
            if callable(log):
                log(f"Récursion détectée sur « {name} » : appel ignoré.", "error")
            return False
        if not callable(resolver):
            if callable(log):
                log("Aucun résolveur de workflow disponible.", "warning")
            return False
        sub = resolver(name)
        if sub is None:
            if callable(log):
                log(f"Sous-workflow « {name} » introuvable.", "warning")
            return False
        runner = (context or {}).get("run_actions")
        call_stack.append(name)
        try:
            if callable(runner):
                runner(sub.actions)
        finally:
            call_stack.pop()
        return True

    def summary(self) -> str:
        return f"Exécuter le workflow « {self.params.get('workflow_name')} »"
