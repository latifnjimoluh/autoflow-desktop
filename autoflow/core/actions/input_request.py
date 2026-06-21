"""Action de **saisie utilisateur** en cours d'exécution (workflow interactif).

Met le workflow en pause pour demander à l'utilisateur une valeur, une
confirmation oui/non, ou un choix dans une liste. Le résultat est stocké en
variable. Le *fournisseur* (``context["input_provider"]``) est injecté par
l'interface (dialogue) ou par les tests (réponse simulée) — le cœur reste
testable sans écran.
"""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec

INPUT_KINDS = {
    "text": "Demander une valeur",
    "confirm": "Demander une confirmation (oui/non)",
    "choice": "Demander de choisir dans une liste",
}


@register
class UserInputAction(Action):
    """Interrompt le workflow pour demander une saisie à l'utilisateur."""

    type_name = "user_input"
    label = "Demander une saisie à l'utilisateur"
    category = "Contrôle"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("kind", "Type de demande", "choice", "text",
                      choices=list(INPUT_KINDS.keys())),
            ParamSpec("prompt", "Question / message", "str", "",
                      supports_vars=True, placeholder="Ex : Quel est votre nom ?"),
            ParamSpec("default", "Valeur par défaut", "str", "",
                      depends_on=("kind", "text")),
            ParamSpec("choices", "Choix (séparés par des virgules)", "str", "",
                      depends_on=("kind", "choice"),
                      placeholder="Ex : Oui, Non, Peut-être"),
            ParamSpec("var_name", "Stocker la réponse dans", "variable", "reponse"),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        provider = (context or {}).get("input_provider")
        store = (context or {}).get("variables")
        kind = str(self.params.get("kind", "text"))
        request = {
            "kind": kind,
            "prompt": str(self._resolve(self.params.get("prompt", ""), context)),
            "default": str(self._resolve(self.params.get("default", ""), context)),
            "choices": [c.strip() for c in str(self.params.get("choices", "")).split(",")
                        if c.strip()],
        }
        if callable(provider):
            response = provider(request)
        else:
            # Aucun fournisseur (exécution non interactive) : valeur par défaut.
            response = request["default"] if kind == "text" else (
                False if kind == "confirm" else (
                    request["choices"][0] if request["choices"] else ""))
        var = str(self.params.get("var_name", "")).strip()
        if store is not None and var:
            store.set(var, response)
        return response

    def summary(self) -> str:
        return f"{INPUT_KINDS.get(str(self.params.get('kind')), 'Saisie')} → {self.params.get('var_name')}"
