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
        type : type logique du champ. Types **abstraits** historiques : ``str``,
            ``text``, ``int``, ``float``, ``bool``, ``keys``, ``choice``,
            ``file``. Types **concrets** v3 (composants guidés) : ``key`` (capture
            de touche + liste cherchable), ``hotkey`` (capture de combinaison),
            ``window`` (liste des fenêtres ouvertes), ``app`` (apps installées /
            parcourir / manuel), ``color`` (sélecteur de couleur), ``variable``
            (liste des variables existantes), ``folder`` (dossier) et
            ``workflow`` (liste des workflows). Un type inconnu retombe sur un
            champ texte (compatibilité ascendante).
        default : valeur par défaut.
        choices : valeurs possibles pour le type ``choice``.
        help : texte d'aide facultatif (infobulle).
        placeholder : exemple affiché en filigrane (ex. « Ex : notepad.exe »).
        supports_vars : si vrai, le champ propose l'insertion de ``{{variable}}``.
        depends_on : couple ``(nom_param, valeur)`` ; le champ n'est affiché que
            si l'autre paramètre vaut cette valeur (champs guidés conditionnels).
    """

    name: str
    label: str
    type: str = "str"
    default: Any = None
    choices: list[Any] | None = None
    help: str = ""
    placeholder: str = ""
    supports_vars: bool = False
    depends_on: tuple[str, Any] | None = None


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
        retries: int = 0,
        retry_delay: float = 0.0,
        on_error: str = "inherit",
        delay_jitter: float = 0.0,
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
        # Politique d'exécution (fonctionnalités timeout/retry & délais humains).
        self.retries = int(retries)
        self.retry_delay = float(retry_delay)
        self.on_error = str(on_error)  # "inherit" | "continue" | "stop"
        self.delay_jitter = float(delay_jitter)

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
        """Sérialise l'action en dictionnaire JSON-compatible.

        Les champs de politique (retries, on_error…) ne sont écrits que s'ils
        diffèrent de leurs valeurs par défaut, afin de garder le JSON compact et
        compatible avec les anciens workflows.
        """
        data: dict[str, Any] = {
            "type": self.type_name,
            "params": dict(self.params),
            "enabled": self.enabled,
            "delay_after": self.delay_after,
        }
        if self.retries:
            data["retries"] = self.retries
        if self.retry_delay:
            data["retry_delay"] = self.retry_delay
        if self.on_error != "inherit":
            data["on_error"] = self.on_error
        if self.delay_jitter:
            data["delay_jitter"] = self.delay_jitter
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        """Reconstruit une action depuis un dictionnaire (compat. ascendante)."""
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
        )

    # -- Contrôle de flux --------------------------------------------------
    def child_groups(self) -> dict[str, list["Action"]]:
        """Renvoie les groupes d'actions enfants (vide pour une action simple).

        Les actions de contrôle de flux (condition, boucle) surchargent cette
        méthode pour exposer leurs sous-séquences, ce qui permet à l'interface
        et au moteur de les parcourir de façon générique.
        """
        return {}

    # -- Aides -------------------------------------------------------------
    def _resolve(self, value: Any, context: dict[str, Any] | None) -> Any:
        """Substitue les gabarits ``{{var}}`` à l'aide du magasin de variables."""
        store = (context or {}).get("variables")
        if store is not None:
            return store.resolve(value)
        return value

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
