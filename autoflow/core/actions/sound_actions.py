"""Actions son & synthèse vocale : énoncer un texte, jouer un son / un bip."""

from __future__ import annotations

from typing import Any

from ...services import tts
from ..registry import register
from .base import Action, ParamSpec


@register
class SpeakAction(Action):
    """Énonce un texte à voix haute (hors-ligne, dégradation propre si absent)."""

    type_name = "speak"
    label = "Énoncer un texte (voix)"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [ParamSpec("text", "Texte à énoncer", "text", "", supports_vars=True,
                          placeholder="Ex : Workflow terminé.")]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        text = str(self._resolve(self.params.get("text", ""), context))
        factory = (context or {}).get("tts_engine")  # injection pour tests
        ok = tts.speak(text, engine_factory=factory)
        if not ok:
            log = (context or {}).get("log")
            if callable(log):
                log("Synthèse vocale indisponible (texte non énoncé).", "warning")
        return ok

    def summary(self) -> str:
        return f"Énoncer : « {self.params.get('text')} »"


@register
class PlaySoundAction(Action):
    """Joue un bip ou un fichier audio (alerte sonore)."""

    type_name = "play_sound"
    label = "Jouer un son / bip"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("mode", "Type", "choice", "beep", choices=["beep", "file"]),
            ParamSpec("path", "Fichier audio (.wav)", "file", "",
                      depends_on=("mode", "file"), supports_vars=True),
            ParamSpec("frequency", "Fréquence du bip (Hz)", "int", 880,
                      depends_on=("mode", "beep"), min_value=37, max_value=32767),
            ParamSpec("duration_ms", "Durée du bip (ms)", "int", 300,
                      depends_on=("mode", "beep"), min_value=10),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        mode = str(self.params.get("mode", "beep"))
        if mode == "file":
            path = str(self._resolve(self.params.get("path", ""), context))
            return tts.play_sound(path, player=(context or {}).get("sound_player"))
        return tts.beep(int(self.params.get("frequency", 880)),
                        int(self.params.get("duration_ms", 300)),
                        player=(context or {}).get("beep_player"))

    def summary(self) -> str:
        if self.params.get("mode") == "file":
            return f"Jouer le son « {self.params.get('path')} »"
        return f"Bip {self.params.get('frequency')} Hz"
