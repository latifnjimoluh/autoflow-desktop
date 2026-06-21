"""Actions : variables globales (partagées, persistées) et secrets (coffre)."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


@register
class SetGlobalAction(Action):
    """Définit une variable **globale** partagée entre tous les workflows."""

    type_name = "set_global"
    label = "Définir une variable globale"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("name", "Nom de la variable globale", "variable", "compteur_global"),
            ParamSpec("value", "Valeur", "str", "", supports_vars=True,
                      placeholder="Ex : {{resultat}}"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("name", "")).strip():
            raise ValueError("Le nom de la variable globale ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        glob = (context or {}).get("globals")
        value = self._resolve(self.params.get("value", ""), context)
        if glob is not None:
            glob.set(str(self.params["name"]).strip(), value)
        return value

    def summary(self) -> str:
        return f"Global {self.params.get('name')} = « {self.params.get('value')} »"


@register
class GetGlobalAction(Action):
    """Lit une variable globale dans une variable d'exécution."""

    type_name = "get_global"
    label = "Lire une variable globale"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("name", "Variable globale à lire", "variable", "compteur_global"),
            ParamSpec("var_name", "Stocker dans la variable", "variable", "valeur"),
            ParamSpec("default", "Valeur par défaut (si absente)", "str", ""),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        glob = (context or {}).get("globals")
        store = (context or {}).get("variables")
        name = str(self.params.get("name", "")).strip()
        default = self._resolve(self.params.get("default", ""), context)
        value = glob.get(name, default) if glob is not None else default
        var = str(self.params.get("var_name", "")).strip()
        if store is not None and var:
            store.set(var, value)
        return value

    def summary(self) -> str:
        return f"Lire global {self.params.get('name')} → {self.params.get('var_name')}"


@register
class GetSecretAction(Action):
    """Charge un secret (déchiffré) dans une variable d'exécution (en mémoire)."""

    type_name = "get_secret"
    label = "Lire un secret (coffre)"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("name", "Nom du secret", "str", "",
                      placeholder="Ex : cle_api_meteo",
                      help="Le secret doit avoir été enregistré dans le coffre."),
            ParamSpec("var_name", "Stocker dans la variable", "variable", "secret"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("name", "")).strip():
            raise ValueError("Le nom du secret ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        vault = (context or {}).get("secrets")
        store = (context or {}).get("variables")
        name = str(self.params.get("name", "")).strip()
        value = ""
        if vault is not None:
            try:
                value = vault.get(name, "") or ""
            except Exception as exc:  # noqa: BLE001 — coffre indisponible
                log = (context or {}).get("log")
                if callable(log):
                    log(f"Secret « {name} » illisible : {exc}", "warning")
        var = str(self.params.get("var_name", "")).strip()
        if store is not None and var:
            store.set(var, value)
        return bool(value)

    def summary(self) -> str:
        return f"Lire le secret « {self.params.get('name')} » → {self.params.get('var_name')}"
