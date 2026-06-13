"""Configuration de la journalisation et horodatage des messages.

Fournit un format horodaté homogène, dans l'esprit des ``print`` horodatés des
scripts d'origine.
"""

from __future__ import annotations

import logging
from datetime import datetime

# Correspondance niveau AutoFlow -> niveau logging standard.
_LEVELS = {
    "info": logging.INFO,
    "action": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def timestamp() -> str:
    """Renvoie l'horodatage courant « HH:MM:SS »."""
    return datetime.now().strftime("%H:%M:%S")


def format_log(message: str, level: str = "info") -> str:
    """Met en forme un message de log horodaté : ``[HH:MM:SS] message``."""
    prefixe = {
        "warning": "⚠ ",
        "error": "✖ ",
        "action": "• ",
    }.get(level, "")
    return f"[{timestamp()}] {prefixe}{message}"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure et renvoie le logger racine d'AutoFlow."""
    logger = logging.getLogger("autoflow")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def to_logging_level(level: str) -> int:
    """Convertit un niveau AutoFlow en niveau du module ``logging``."""
    return _LEVELS.get(level, logging.INFO)
