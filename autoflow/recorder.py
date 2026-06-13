"""Mode enregistrement : capture des clics et frappes réels via ``pynput``.

Les événements capturés sont convertis en actions AutoFlow éditables. ``pynput``
est importé **paresseusement** pour préserver l'import en environnement headless.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from .core.registry import create_action


class Recorder:
    """Enregistre clics et frappes et les transforme en liste d'actions.

    L'appelant peut fournir ``on_action`` pour être notifié en direct de chaque
    action capturée. Les délais réels entre événements sont reportés en
    ``delay_after`` afin de rejouer le rythme de l'utilisateur.
    """

    def __init__(self, on_action: Callable[[Any], None] | None = None) -> None:
        self.on_action = on_action or (lambda _a: None)
        self.actions: list[Any] = []
        self._mouse_listener = None
        self._keyboard_listener = None
        self._last_time: float | None = None

    # -- Conversion d'événements ------------------------------------------
    def _elapsed(self) -> float:
        """Renvoie le temps écoulé depuis le dernier événement (et le met à jour)."""
        now = time.monotonic()
        delay = 0.0 if self._last_time is None else max(0.0, now - self._last_time)
        self._last_time = now
        return round(delay, 3)

    def _add(self, action: Any) -> None:
        """Ajoute une action capturée et notifie l'appelant."""
        self.actions.append(action)
        self.on_action(action)

    def record_click(self, x: int, y: int, button: str = "left") -> Any:
        """Crée une action de clic à partir d'un événement souris."""
        action = create_action(
            "click",
            params={"x": int(x), "y": int(y), "button": button, "clicks": 1},
            delay_after=self._elapsed(),
        )
        self._add(action)
        return action

    def record_text(self, text: str) -> Any:
        """Crée une action de saisie de texte à partir d'un événement clavier."""
        action = create_action(
            "type_text",
            params={"text": text},
            delay_after=self._elapsed(),
        )
        self._add(action)
        return action

    def record_key(self, key: str) -> Any:
        """Crée une action d'appui de touche spéciale (enter, tab, esc…)."""
        action = create_action(
            "key_press",
            params={"key": key},
            delay_after=self._elapsed(),
        )
        self._add(action)
        return action

    # -- Écoute réelle (pynput) -------------------------------------------
    def start(self) -> bool:
        """Démarre la capture réelle des entrées. Renvoie ``True`` si possible."""
        try:
            from pynput import keyboard, mouse  # import paresseux volontaire
        except Exception:  # noqa: BLE001 - indisponible (headless / non installé)
            return False

        self._last_time = time.monotonic()

        def on_click(x, y, button, pressed):  # pragma: no cover - E/S réelles
            if pressed:
                name = getattr(button, "name", "left")
                self.record_click(int(x), int(y), name)

        def on_press(key):  # pragma: no cover - E/S réelles
            char = getattr(key, "char", None)
            if char is not None:
                self.record_text(char)
            else:
                name = str(key).replace("Key.", "")
                self.record_key(name)

        try:
            self._mouse_listener = mouse.Listener(on_click=on_click)
            self._keyboard_listener = keyboard.Listener(on_press=on_press)
            self._mouse_listener.start()
            self._keyboard_listener.start()
        except Exception:  # noqa: BLE001 - pas d'affichage disponible
            self.stop()
            return False
        return True

    def stop(self) -> list[Any]:
        """Arrête la capture et renvoie la liste des actions enregistrées."""
        for listener in (self._mouse_listener, self._keyboard_listener):
            if listener is not None:
                try:
                    listener.stop()
                except Exception:  # noqa: BLE001
                    pass
        self._mouse_listener = None
        self._keyboard_listener = None
        return self.actions
