"""Élévation douce via ``QGraphicsDropShadowEffect`` (Qt n'a pas de box-shadow).

Trois niveaux cohérents avec :data:`autoflow.ui.theme.tokens.ELEVATION`. Toutes
les fonctions sont **sans effet de bord** hors écran : si Qt n'est pas
disponible, elles renvoient ``None`` sans lever d'exception (sûr en tests).
"""

from __future__ import annotations

from typing import Any

from . import tokens


def apply_elevation(widget: Any, level: int = 1) -> Any | None:
    """Applique une ombre portée douce de niveau ``level`` (1–3) à ``widget``.

    Renvoie l'effet créé (ou ``None`` si Qt indisponible). L'ombre est neutre
    (noir translucide), donc lisible dans les deux thèmes.
    """
    spec = tokens.ELEVATION.get(level, tokens.ELEVATION[1])
    try:
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
    except Exception:  # noqa: BLE001 — pas d'écran/Qt : dégradation propre
        return None

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(spec["blur"])
    effect.setColor(QColor(0, 0, 0, spec["alpha"]))
    effect.setOffset(0, spec["dy"])
    widget.setGraphicsEffect(effect)
    return effect
