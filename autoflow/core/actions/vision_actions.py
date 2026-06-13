"""Actions de perception de l'écran : recherche d'image, pixel, OCR."""

from __future__ import annotations

from typing import Any

from .. import conditions
from ..registry import register
from .base import Action, ParamSpec


def _locate(path: str, confidence: float, region, inputs, context):
    """Localise une image via OpenCV si dispo, sinon via pyautogui."""
    vision = (context or {}).get("vision")
    if vision is not None and vision.is_available():
        return vision.locate_center(path, confidence=confidence, region=region)
    return inputs.locate_center(path, confidence=confidence)


@register
class FindImageAction(Action):
    """Recherche une image et stocke le centre trouvé dans des variables."""

    type_name = "find_image"
    label = "Trouver une image"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("image_path", "Image", "file", ""),
            ParamSpec("confidence", "Confiance", "float", 0.8),
            ParamSpec("var_name", "Variable (x,y)", "str", "image_pos"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("image_path", "")).strip():
            raise ValueError("Le chemin de l'image ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        path = str(self._resolve(self.params.get("image_path", ""), context))
        location = _locate(path, float(self.params.get("confidence", 0.8)), None,
                           inputs, context)
        store = (context or {}).get("variables")
        var = str(self.params.get("var_name", "")).strip()
        log = (context or {}).get("log")
        if location is None:
            if callable(log):
                log(f"Image « {path} » introuvable à l'écran.", "warning")
            return None
        if store is not None and var:
            store.set(var, f"{location[0]},{location[1]}")
            store.set(f"{var}_x", location[0])
            store.set(f"{var}_y", location[1])
        return location

    def summary(self) -> str:
        return f"Trouver l'image « {self.params.get('image_path')} »"


@register
class WaitForPixelAction(Action):
    """Attend qu'un pixel atteigne une couleur (avec tolérance et timeout)."""

    type_name = "wait_for_pixel"
    label = "Attendre une couleur de pixel"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("x", "X", "int", 0),
            ParamSpec("y", "Y", "int", 0),
            ParamSpec("color", "Couleur (#RRGGBB)", "str", "#ffffff"),
            ParamSpec("tolerance", "Tolérance", "int", 10),
            ParamSpec("timeout", "Délai max (s)", "float", 10.0),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        sleep = (context or {}).get("sleep") or _default_sleep
        deadline = float(self.params.get("timeout", 10.0))
        elapsed = 0.0
        step = 0.3
        while elapsed <= deadline:
            if conditions._pixel_matches(self.params, inputs):
                return True
            sleep(step)
            elapsed += step
        log = (context or {}).get("log")
        if callable(log):
            log("Couleur de pixel non atteinte (timeout).", "warning")
        return False

    def summary(self) -> str:
        return (f"Attendre pixel ({self.params.get('x')}, {self.params.get('y')}) "
                f"= {self.params.get('color')}")


@register
class ReadTextAction(Action):
    """Lit le texte d'une région de l'écran (OCR Tesseract) dans une variable."""

    type_name = "read_text"
    label = "Lire du texte (OCR)"
    category = "Écran"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("region", "Région", "bool", True),
            ParamSpec("x", "X", "int", 0),
            ParamSpec("y", "Y", "int", 0),
            ParamSpec("width", "Largeur", "int", 200),
            ParamSpec("height", "Hauteur", "int", 50),
            ParamSpec("lang", "Langue", "str", "fra"),
            ParamSpec("var_name", "Variable", "str", "texte_ocr"),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        ocr = (context or {}).get("ocr")
        store = (context or {}).get("variables")
        log = (context or {}).get("log")
        var = str(self.params.get("var_name", "")).strip()
        if ocr is None or not ocr.is_available():
            if callable(log):
                log("Tesseract introuvable : action OCR ignorée. "
                    "Installez Tesseract et indiquez son chemin dans les réglages.",
                    "warning")
            if store is not None and var:
                store.set(var, "")
            return ""
        region = None
        if self.params.get("region"):
            region = (int(self.params["x"]), int(self.params["y"]),
                      int(self.params["width"]), int(self.params["height"]))
        text = ocr.read_region(region, lang=str(self.params.get("lang", "fra")))
        if store is not None and var:
            store.set(var, text)
        if callable(log):
            log(f"OCR : {len(text)} caractère(s) lus → {var}.", "info")
        return text

    def summary(self) -> str:
        return f"Lire du texte (OCR) → {self.params.get('var_name')}"


def _default_sleep(seconds: float) -> None:  # pragma: no cover - repli hors moteur
    import time

    time.sleep(seconds)
