"""Classe d'action abstraite et schéma de paramètres.

Chaque action concrète décrit ses paramètres via :class:`ParamSpec`, ce qui
permet à l'interface de générer automatiquement le formulaire d'édition.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParamSpec:
    """Description d'un paramètre d'action pour la génération de formulaire.

    Attributs :
        name : identifiant technique du paramètre (clé dans ``params``).
        label : libellé affiché à l'utilisateur (en français).
        type : type logique parmi ``str``, ``text``, ``int``, ``float``,
            ``bool``, ``keys``, ``choice``, ``file`` ou ``coord``.
        default : valeur par défaut.
        choices : valeurs possibles pour le type ``choice``.
        help : texte d'aide facultatif.
    """

    name: str
    label: str
    type: str = "str"
    default: Any = None
    choices: list[Any] | None = None
    help: str = ""


class Action(abc.ABC):
    """Action abstraite : brique élémentaire d'un workflow.

    Une action porte ses ``params``, un drapeau ``enabled`` et un ``delay_after``
    (pause en secondes appliquée après son exécution par le moteur).
    """

    #: Identifiant de type (sérialisation, registre). À surcharger.
    type_name: str = ""
    #: Libellé affiché dans l'interface (français). À surcharger.
    label: str = ""
    #: Catégorie pour le regroupement dans les menus.
    category: str = "Général"

    def __init__(
        self,
        params: dict[str, Any] | None = None,
        enabled: bool = True,
        delay_after: float = 0.0,
    ) -> None:
        # Initialise les paramètres avec les valeurs par défaut du schéma,
        # puis applique les valeurs fournies.
        self.params: dict[str, Any] = {}
        for spec in self.param_specs():
            self.params[spec.name] = _copy_default(spec.default)
        if params:
            self.params.update(params)
        self.enabled = bool(enabled)
        self.delay_after = float(delay_after)

    # -- Schéma ------------------------------------------------------------
    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        """Renvoie la liste des paramètres acceptés par l'action."""
        return []

    # -- Exécution ---------------------------------------------------------
    @abc.abstractmethod
    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        """Exécute l'action.

        Args:
            inputs : façade d'entrées (souris/clavier), cf. ``InputBackend``.
            windows : façade de gestion des fenêtres, cf. ``WindowsBackend``.
            context : dictionnaire partagé entre actions d'une même exécution.
        """

    def validate(self) -> None:
        """Valide les paramètres. Lève :class:`ValueError` si invalides."""

    # -- Présentation ------------------------------------------------------
    def summary(self) -> str:
        """Renvoie un résumé lisible de l'action (affiché dans la liste)."""
        return self.label or self.type_name

    # -- (Dé)sérialisation -------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'action en dictionnaire JSON-compatible."""
        return {
            "type": self.type_name,
            "params": dict(self.params),
            "enabled": self.enabled,
            "delay_after": self.delay_after,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        """Reconstruit une action depuis un dictionnaire."""
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
        )

    # -- Aides -------------------------------------------------------------
    def _require_number(self, name: str) -> float:
        """Valide qu'un paramètre est un nombre et le renvoie."""
        value = self.params.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"Le paramètre '{name}' doit être numérique.")
        return float(value)

    def __repr__(self) -> str:  # pragma: no cover - confort de débogage
        return f"<{type(self).__name__} {self.params!r} enabled={self.enabled}>"


def _copy_default(value: Any) -> Any:
    """Copie superficielle des valeurs par défaut mutables (listes)."""
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value
