"""Identité visuelle d'AutoFlow : logo/icône d'application (peint, hors-ligne).

L'icône est **dessinée par programme** à partir des tokens d'accent : un carré
arrondi indigo portant un éclair blanc stylisé (« flux »). Aucun fichier binaire
requis, fonctionnement 100 % hors-ligne, et rendu net à toute taille.

Un SVG équivalent est aussi disponible sous ``assets/logo.svg`` (déposé par ce
module au besoin) pour le packaging / la documentation.
"""

from __future__ import annotations

from typing import Any

from .theme import tokens

APP_NAME = "AutoFlow"
APP_TAGLINE = "Automatisation visuelle du PC"
REPO_URL = "https://github.com/latifnjimoluh/autoflow-desktop"


def _version() -> str:
    """Renvoie la version du paquet (repli ``0.0.0`` si indisponible)."""
    try:
        from importlib.metadata import version
        return version("autoflow")
    except Exception:  # noqa: BLE001
        return "1.0.0"


VERSION = _version()


def app_icon(size: int = 256) -> Any | None:
    """Construit le ``QIcon`` de l'application (carré arrondi + éclair).

    Renvoie ``None`` si Qt n'est pas disponible (sûr hors écran).
    """
    try:
        from PySide6.QtCore import QPointF, QRectF, Qt
        from PySide6.QtGui import (
            QBrush,
            QColor,
            QIcon,
            QLinearGradient,
            QPainter,
            QPainterPath,
            QPixmap,
            QPolygonF,
        )
    except Exception:  # noqa: BLE001
        return None

    accent = tokens.ACCENT
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Fond : carré arrondi avec dégradé d'accent.
    radius = size * 0.22
    rect = QRectF(size * 0.06, size * 0.06, size * 0.88, size * 0.88)
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, QColor(accent["accent"]))
    grad.setColorAt(1.0, QColor(accent["accent_active"]))
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.fillPath(path, QBrush(grad))

    # Éclair blanc stylisé (le « flux »).
    w, h = size, size
    bolt = QPolygonF([
        QPointF(w * 0.56, h * 0.20),
        QPointF(w * 0.34, h * 0.54),
        QPointF(w * 0.48, h * 0.54),
        QPointF(w * 0.44, h * 0.80),
        QPointF(w * 0.66, h * 0.46),
        QPointF(w * 0.52, h * 0.46),
    ])
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent["on_accent"]))
    painter.drawPolygon(bolt)
    painter.end()

    return QIcon(pix)
