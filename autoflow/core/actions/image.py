"""Actions avancées basées sur la reconnaissance d'image à l'écran."""

from __future__ import annotations

from typing import Any

from ..registry import register
from .base import Action, ParamSpec


def _locate(path: str, confidence: float, inputs, context):
    """Localise une image via OpenCV si disponible, sinon via pyautogui."""
    vision = (context or {}).get("vision")
    if vision is not None and vision.is_available():
        return vision.locate_center(path, confidence=confidence)
    return inputs.locate_center(path, confidence=confidence)


@register
class WaitForImageAction(Action):
    """Attend qu'une image apparaisse à l'écran (automatisation conditionnelle)."""

    type_name = "wait_for_image"
    label = "Attendre une image"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Image à rechercher", "file", ""),
            ParamSpec("timeout", "Délai max (s)", "float", 10.0),
            ParamSpec("confidence", "Confiance (0-1)", "float", 0.9),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin de l'image ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        deadline = float(self.params.get("timeout", 10.0))
        sleep = (context or {}).get("sleep") or _default_sleep
        elapsed = 0.0
        step = 0.5
        while elapsed <= deadline:
            location = _locate(
                str(self.params["path"]),
                float(self.params.get("confidence", 0.9)),
                inputs, context,
            )
            if location is not None:
                if context is not None:
                    context["last_image_location"] = location
                return location
            sleep(step)
            elapsed += step
        log = (context or {}).get("log")
        if callable(log):
            log(f"Image '{self.params['path']}' non trouvée (timeout).", "warning")
        return None

    def summary(self) -> str:
        return f"Attendre l'image « {self.params.get('path')} »"


@register
class ClickImageAction(Action):
    """Localise une image à l'écran puis clique en son centre."""

    type_name = "click_image"
    label = "Cliquer sur une image"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Image à cliquer", "file", ""),
            ParamSpec("confidence", "Confiance (0-1)", "float", 0.9),
            ParamSpec("button", "Bouton", "choice", "left",
                      choices=["left", "right", "middle"]),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin de l'image ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        location = _locate(
            str(self.params["path"]),
            float(self.params.get("confidence", 0.9)),
            inputs, context,
        )
        if location is None:
            log = (context or {}).get("log")
            if callable(log):
                log(f"Image '{self.params['path']}' introuvable à l'écran.",
                    "warning")
            return None
        x, y = location
        return inputs.click(x=int(x), y=int(y), button=str(self.params.get("button", "left")))

    def summary(self) -> str:
        return f"Cliquer sur l'image « {self.params.get('path')} »"


def _default_sleep(seconds: float) -> None:  # pragma: no cover - repli hors moteur
    import time

    time.sleep(seconds)
