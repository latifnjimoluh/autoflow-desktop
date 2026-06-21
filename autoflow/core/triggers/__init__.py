"""Déclencheurs événementiels d'AutoFlow (automatisation réactive).

Un *déclencheur* écoute un événement (fenêtre, fichier, presse-papiers,
inactivité/session, webhook) et **démarre un workflow**. Ce système est parallèle
au registre d'actions et complète la planification existante.

L'import de ce paquet enregistre tous les types de déclencheurs.
"""

from __future__ import annotations

from . import (  # noqa: F401
    clipboard_trigger,
    file_trigger,
    idle_trigger,
    webhook_trigger,
    window_trigger,
)
from .base import Trigger, TriggerEvent
from .registry import (
    available_triggers,
    create_trigger,
    register_trigger,
    trigger_from_dict,
)

__all__ = [
    "Trigger",
    "TriggerEvent",
    "create_trigger",
    "trigger_from_dict",
    "register_trigger",
    "available_triggers",
]
