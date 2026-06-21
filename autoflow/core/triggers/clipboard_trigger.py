"""Déclencheur par presse-papiers : démarre un workflow quand le contenu change.

Option : ne déclencher que si le nouveau contenu correspond à une **regex**. La
détection (``detect``) est pure/testable ; la surveillance live interroge le
presse-papiers périodiquement.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from .base import ParamSpec, Trigger, TriggerEvent
from .registry import register_trigger


@register_trigger
class ClipboardTrigger(Trigger):
    """Démarre un workflow au changement du presse-papiers."""

    type_name = "clipboard_event"
    label = "Déclencheur : presse-papiers"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("pattern", "Ne déclencher que si ça correspond (regex, optionnel)",
                      "str", "", placeholder=r"Ex : https?://\S+"),
            ParamSpec("interval", "Intervalle de vérification (s)", "float", 0.7,
                      min_value=0.1),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._last: str | None = None
        self._timer: threading.Timer | None = None
        self._clipboard: Any = None

    def detect(self, content: str) -> TriggerEvent | None:
        """Détecte un changement (et la correspondance regex éventuelle)."""
        if content is None:
            return None
        if self._last is None:
            # Premier relevé : on mémorise sans déclencher.
            self._last = content
            return None
        if content == self._last:
            return None
        self._last = content
        pattern = str(self.params.get("pattern", "")).strip()
        if pattern:
            try:
                if not re.search(pattern, content):
                    return None
            except re.error:
                return None
        return TriggerEvent(
            trigger_type=self.type_name,
            message="Presse-papiers modifié",
            variables={"clipboard": content})

    # -- Live --------------------------------------------------------------
    def bind_clipboard(self, clipboard: Any) -> None:
        self._clipboard = clipboard

    def _poll_once(self) -> None:
        if self._clipboard is None:
            return
        content = self._clipboard.get_text() if hasattr(self._clipboard, "get_text") else ""
        event = self.detect(content)
        if event is not None:
            self.fire(event)

    def _start(self) -> bool:
        if self._clipboard is None:
            return False
        self._schedule()
        return True

    def _schedule(self) -> None:
        interval = float(self.params.get("interval", 0.7) or 0.7)
        self._timer = threading.Timer(interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:  # pragma: no cover - boucle temporisée
        if not self.is_running():
            return
        try:
            self._poll_once()
        finally:
            if self.is_running():
                self._schedule()

    def _stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def summary(self) -> str:
        pat = self.params.get("pattern")
        return f"Presse-papiers modifié{f' (~ {pat})' if pat else ''}"
