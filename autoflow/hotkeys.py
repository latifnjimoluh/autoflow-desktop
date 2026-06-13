"""Écoute globale du clavier pour l'arrêt d'urgence (via ``pynput``).

``pynput`` est importé **paresseusement** : ce module s'importe sans erreur en
environnement sans affichage. Le listener tourne dans son propre thread et
appelle une fonction de rappel lorsque le raccourci configuré est détecté —
y compris pendant l'exécution d'un workflow.
"""

from __future__ import annotations

from typing import Callable


def to_pynput_hotkey(combo: str) -> str:
    """Convertit « ctrl+shift+q » au format pynput « <ctrl>+<shift>+q »."""
    parts = [p.strip().lower() for p in combo.replace(",", "+").split("+") if p.strip()]
    modifiers = {"ctrl", "shift", "alt", "cmd", "ctrl_l", "ctrl_r",
                 "alt_l", "alt_r", "shift_l", "shift_r", "super"}
    tokens = []
    for part in parts:
        if part in modifiers or len(part) > 1:
            tokens.append(f"<{part}>")
        else:
            tokens.append(part)
    return "+".join(tokens)


class EmergencyHotkey:
    """Écoute un raccourci global et déclenche un rappel d'arrêt d'urgence."""

    def __init__(self, combo: str = "ctrl+shift+q",
                 on_trigger: Callable[[], None] | None = None) -> None:
        self.combo = combo
        self.on_trigger = on_trigger or (lambda: None)
        self._listener = None

    def start(self) -> bool:
        """Démarre l'écoute globale. Renvoie ``True`` si elle a pu démarrer."""
        try:
            from pynput import keyboard  # import paresseux volontaire
        except Exception:  # noqa: BLE001 - indisponible (headless / non installé)
            return False
        mapping = {to_pynput_hotkey(self.combo): self._fire}
        try:
            self._listener = keyboard.GlobalHotKeys(mapping)
            self._listener.start()
        except Exception:  # noqa: BLE001 - pas d'affichage disponible
            self._listener = None
            return False
        return True

    def _fire(self) -> None:
        """Appelle le rappel d'arrêt d'urgence."""
        self.on_trigger()

    def stop(self) -> None:
        """Arrête l'écoute globale."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:  # noqa: BLE001
                pass
            self._listener = None


class GlobalHotkeyManager:
    """Écoute plusieurs raccourcis globaux (un par workflow déclenchable)."""

    def __init__(self) -> None:
        self._bindings: dict[str, Callable[[], None]] = {}
        self._listener = None

    def set_bindings(self, bindings: dict[str, Callable[[], None]]) -> None:
        """Définit la table ``raccourci -> rappel`` et (re)démarre l'écoute."""
        self._bindings = dict(bindings)
        self.restart()

    def restart(self) -> bool:
        """(Re)démarre le listener avec les raccourcis courants."""
        self.stop()
        if not self._bindings:
            return False
        try:
            from pynput import keyboard  # import paresseux

            mapping = {to_pynput_hotkey(combo): cb
                       for combo, cb in self._bindings.items()}
            self._listener = keyboard.GlobalHotKeys(mapping)
            self._listener.start()
        except Exception:  # noqa: BLE001 - headless / conflit / non installé
            self._listener = None
            return False
        return True

    def stop(self) -> None:
        """Arrête l'écoute."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:  # noqa: BLE001
                pass
            self._listener = None
