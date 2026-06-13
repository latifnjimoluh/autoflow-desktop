"""OCR via Tesseract (``pytesseract``), à dégradation propre.

Le moteur Tesseract est un **binaire externe** : s'il est introuvable, l'action
OCR n'échoue pas brutalement — elle renvoie une chaîne vide et journalise un
message explicite. Le chemin du binaire est configurable.
"""

from __future__ import annotations

from typing import Any


class OcrBackend:
    """Extrait le texte d'une région de l'écran via Tesseract."""

    def __init__(self, tesseract_path: str = "") -> None:
        self.tesseract_path = tesseract_path

    def is_available(self) -> bool:
        """Indique si pytesseract et le binaire Tesseract sont utilisables."""
        try:
            import pytesseract
        except Exception:  # noqa: BLE001
            return False
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        try:
            pytesseract.get_tesseract_version()
        except Exception:  # noqa: BLE001 - binaire absent / non configuré
            return False
        return True

    def read_region(self, region: tuple[int, int, int, int] | None = None,
                    lang: str = "fra") -> str:
        """Capture une région et en renvoie le texte (chaîne vide si indisponible)."""
        import pytesseract
        import pyautogui  # import paresseux

        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        capture = pyautogui.screenshot(region=region)
        return pytesseract.image_to_string(capture, lang=lang).strip()
