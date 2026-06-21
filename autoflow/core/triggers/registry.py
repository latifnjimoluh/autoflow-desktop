"""Registre / fabrique des types de déclencheurs (parallèle au registre d'actions)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .base import Trigger

_REGISTRY: dict[str, type[Trigger]] = {}


class UnknownTriggerError(KeyError):
    """Levée pour un type de déclencheur inconnu."""


def register_trigger(cls: type[Trigger]) -> type[Trigger]:
    """Enregistre une classe de déclencheur d'après son ``type_name``."""
    type_name = getattr(cls, "type_name", "")
    if not type_name:
        raise ValueError(f"La classe {cls!r} doit définir un 'type_name'.")
    if type_name in _REGISTRY and _REGISTRY[type_name] is not cls:
        raise ValueError(f"Déclencheur déjà enregistré : {type_name!r}.")
    _REGISTRY[type_name] = cls
    return cls


def get_trigger_class(type_name: str) -> type[Trigger]:
    try:
        return _REGISTRY[type_name]
    except KeyError as exc:
        raise UnknownTriggerError(
            f"Déclencheur inconnu : {type_name!r}. Disponibles : {sorted(_REGISTRY)}"
        ) from exc


def create_trigger(type_name: str, params: dict[str, Any] | None = None) -> Trigger:
    return get_trigger_class(type_name)(params=params)


def trigger_from_dict(data: dict[str, Any]) -> Trigger:
    if "type" not in data:
        raise ValueError("Données de déclencheur invalides : 'type' manquant.")
    return get_trigger_class(data["type"]).from_dict(data)


def available_triggers() -> list[tuple[str, str]]:
    """Liste ``(type_name, libellé)`` triée par libellé."""
    items = [(name, getattr(cls, "label", name)) for name, cls in _REGISTRY.items()]
    return sorted(items, key=lambda i: i[1].lower())


def all_trigger_classes() -> dict[str, type[Trigger]]:
    return dict(_REGISTRY)
