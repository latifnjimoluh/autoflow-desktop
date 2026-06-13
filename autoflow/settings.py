"""Réglages applicatifs persistants (JSON).

Regroupe en un point unique : failsafe, pause pyautogui, raccourci d'arrêt
d'urgence, chemin de Tesseract, thème, langue, notifications, démarrage auto.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_DEFAULTS = {
    "failsafe": True,
    "pyautogui_pause": 0.05,
    "emergency_hotkey": "ctrl+shift+q",
    "tesseract_path": "",
    "theme": "dark",          # "dark" | "light"
    "language": "fr",         # "fr" | "en"
    "notifications": True,
    "autostart": False,
    "minimize_to_tray": True,
    "active_profile": "Défaut",
}


@dataclass
class Settings:
    """Réglages d'AutoFlow, sérialisables en JSON et tolérants à l'absence."""

    failsafe: bool = True
    pyautogui_pause: float = 0.05
    emergency_hotkey: str = "ctrl+shift+q"
    tesseract_path: str = ""
    theme: str = "dark"
    language: str = "fr"
    notifications: bool = True
    autostart: bool = False
    minimize_to_tray: bool = True
    active_profile: str = "Défaut"

    def to_dict(self) -> dict[str, Any]:
        """Sérialise les réglages."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Settings":
        """Reconstruit les réglages (champs inconnus ignorés, manquants = défaut)."""
        data = data or {}
        valid = {k: data.get(k, v) for k, v in _DEFAULTS.items()}
        return cls(**valid)

    # -- Persistance -------------------------------------------------------
    def save(self, path: str | Path) -> Path:
        """Enregistre les réglages dans un fichier JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        """Charge les réglages depuis un fichier JSON (défauts si absent/illisible)."""
        path = Path(path)
        if not path.exists():
            return cls()
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return cls()


def settings_path() -> Path:
    """Renvoie le chemin du fichier de réglages dans le dossier de données."""
    from .persistence import store

    return store.data_dir() / "settings.json"


def load_settings() -> Settings:
    """Charge les réglages depuis l'emplacement standard."""
    return Settings.load(settings_path())


def save_settings(settings: Settings) -> Path:
    """Enregistre les réglages à l'emplacement standard."""
    return settings.save(settings_path())
