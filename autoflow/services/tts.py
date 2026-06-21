"""Synthèse vocale (TTS) et bip système — **import paresseux, dégradation propre**.

``pyttsx3`` (hors-ligne) est importé seulement à l'usage : s'il est absent, la
fonction renvoie ``False`` sans lever. Idem pour le bip (``winsound`` sous
Windows, repli silencieux ailleurs).
"""

from __future__ import annotations

from pathlib import Path


def speak(text: str, engine_factory=None) -> bool:
    """Énonce ``text`` à voix haute. Renvoie ``True`` si la synthèse a eu lieu.

    ``engine_factory`` permet d'injecter un faux moteur en test.
    """
    if not str(text).strip():
        return False
    try:
        if engine_factory is None:
            import pyttsx3
            engine_factory = pyttsx3.init
        engine = engine_factory()
        engine.say(str(text))
        engine.runAndWait()
        return True
    except Exception:  # noqa: BLE001 — voix indisponible : dégradation propre
        return False


def beep(frequency: int = 880, duration_ms: int = 300, player=None) -> bool:
    """Émet un bip. Renvoie ``True`` si joué. ``player`` injectable (test)."""
    try:
        if player is not None:
            player(frequency, duration_ms)
            return True
        import winsound  # Windows uniquement
        winsound.Beep(int(frequency), int(duration_ms))
        return True
    except Exception:  # noqa: BLE001
        return False


def play_sound(path: str, player=None) -> bool:
    """Joue un fichier audio (``.wav`` sous Windows). Dégradation propre."""
    if player is not None:
        player(path)
        return True
    if not Path(str(path)).exists():
        return False
    try:
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    except Exception:  # noqa: BLE001
        return False
