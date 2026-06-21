"""Catalogue des actions d'AutoFlow.

L'import de ce paquet déclenche l'enregistrement de toutes les actions dans le
registre (via le décorateur ``@register`` appliqué à chaque classe).
"""

from __future__ import annotations

# Import des modules : chaque classe se sert du décorateur @register et
# s'inscrit donc automatiquement au registre lors de cet import.
from . import (  # noqa: F401
    activate_window,
    click,
    compound_condition,
    data_actions,
    drag,
    email_action,
    error_block,
    file_actions,
    flow,
    global_actions,
    hotkey,
    http_action,
    image,
    input_request,
    key_press,
    launch_app,
    move_mouse,
    screenshot,
    scroll,
    sound_actions,
    system,
    system_power,
    text_actions,
    type_text,
    ui_target,
    variable_actions,
    vision_actions,
    wait,
    wait_for_window,
)
from .base import Action, ParamSpec

__all__ = ["Action", "ParamSpec"]
