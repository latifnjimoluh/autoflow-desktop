"""Registre / fabrique des types d'actions.

Chaque classe d'action s'enregistre via le décorateur :func:`register`. Ajouter
un nouveau type d'action ne nécessite donc qu'une nouvelle classe décorée — le
reste de l'application (interface comprise) la découvre automatiquement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - uniquement pour le typage
    from .actions.base import Action

# Registre interne : identifiant de type -> classe d'action.
_REGISTRY: dict[str, type[Action]] = {}


class UnknownActionError(KeyError):
    """Levée lorsqu'un type d'action inconnu est demandé."""


def register(cls: type[Action]) -> type[Action]:
    """Enregistre une classe d'action d'après son attribut ``type_name``.

    Utilisable comme décorateur de classe. Lève :class:`ValueError` si la classe
    n'a pas de ``type_name`` ou si le type est déjà enregistré.
    """
    type_name = getattr(cls, "type_name", "")
    if not type_name:
        raise ValueError(f"La classe {cls!r} doit définir un 'type_name' non vide.")
    if type_name in _REGISTRY and _REGISTRY[type_name] is not cls:
        raise ValueError(f"Type d'action déjà enregistré : {type_name!r}.")
    _REGISTRY[type_name] = cls
    return cls


def get_action_class(type_name: str) -> type[Action]:
    """Renvoie la classe associée à ``type_name`` ou lève ``UnknownActionError``."""
    try:
        return _REGISTRY[type_name]
    except KeyError as exc:
        raise UnknownActionError(
            f"Type d'action inconnu : {type_name!r}. "
            f"Types disponibles : {sorted(_REGISTRY)}"
        ) from exc


def create_action(
    type_name: str,
    params: dict[str, Any] | None = None,
    enabled: bool = True,
    delay_after: float = 0.0,
) -> Action:
    """Instancie une action de type ``type_name`` avec les paramètres fournis."""
    cls = get_action_class(type_name)
    return cls(params=params, enabled=enabled, delay_after=delay_after)


def action_from_dict(data: dict[str, Any]) -> Action:
    """Reconstruit une action depuis sa forme sérialisée (dict)."""
    if "type" not in data:
        raise ValueError("Données d'action invalides : clé 'type' manquante.")
    cls = get_action_class(data["type"])
    return cls.from_dict(data)


def available_types() -> list[tuple[str, str]]:
    """Renvoie la liste ``(type_name, libellé)`` triée par libellé français."""
    items = [(name, getattr(cls, "label", name)) for name, cls in _REGISTRY.items()]
    return sorted(items, key=lambda item: item[1].lower())


def all_classes() -> dict[str, type[Action]]:
    """Renvoie une copie du registre (type_name -> classe)."""
    return dict(_REGISTRY)


def clear_registry() -> None:
    """Vide le registre (réservé aux tests)."""
    _REGISTRY.clear()
