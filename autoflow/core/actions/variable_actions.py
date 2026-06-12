"""Actions de manipulation des variables d'exécution."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class SetVariableAction(Action):
    """Définit une variable (la valeur peut contenir des gabarits ``{{var}}``)."""

    type_name = "set_variable"
    label = "Définir une variable"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("name", "Nom de la variable", "variable", "ma_variable"),
            ParamSpec("value", "Valeur", "str", "", supports_vars=True,
                      placeholder="Ex : Bonjour {{date}}"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("name", "")).strip():
            raise ValueError("Le nom de la variable ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        store = (context or {}).get("variables")
        value = self._resolve(self.params.get("value", ""), context)
        if store is not None:
            store.set(str(self.params["name"]).strip(), value)
        return value

    def summary(self) -> str:
        return f"{self.params.get('name')} = « {self.params.get('value')} »"


@register
class IncrementVariableAction(Action):
    """Incrémente une variable numérique (créée à 0 si absente)."""

    type_name = "increment_variable"
    label = "Incrémenter une variable"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("name", "Variable à incrémenter", "variable", "compteur"),
            ParamSpec("by", "Pas (valeur ajoutée)", "float", 1.0),
        ]

    def validate(self) -> None:
        if not str(self.params.get("name", "")).strip():
            raise ValueError("Le nom de la variable ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        store = (context or {}).get("variables")
        if store is not None:
            return store.increment(str(self.params["name"]).strip(),
                                   float(self.params.get("by", 1.0)))
        return None

    def summary(self) -> str:
        return f"{self.params.get('name')} += {self.params.get('by')}"
