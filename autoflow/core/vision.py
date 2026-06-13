"""Reconnaissance d'image à l'écran via OpenCV (import paresseux).

``cv2``/``numpy`` ne sont importés qu'à l'utilisation réelle. En leur absence,
:meth:`VisionBackend.is_available` renvoie ``False`` et les actions de vision se
dégradent proprement (message clair, aucune exception non gérée).
"""

from __future__ import annotations

from typing import Any


class VisionBackend:
    """Localise une image-modèle à l'écran avec un seuil de confiance."""

    def __init__(self, inputs: Any = None) -> None:
        self._inputs = inputs

    def is_available(self) -> bool:
        """Indique si OpenCV est disponible."""
        try:
            import cv2  # noqa: F401
            import numpy  # noqa: F401
        except Exception:  # noqa: BLE001
            return False
        return True

    def locate_center(self, template_path: str, confidence: float = 0.8,
                      region: tuple[int, int, int, int] | None = None) -> tuple[int, int] | None:
        """Renvoie le centre de la meilleure correspondance, ou ``None``.

        ``region`` = (x, y, largeur, hauteur) restreint la zone de recherche.
        """
        import cv2
        import numpy as np
        import pyautogui  # import paresseux

        capture = pyautogui.screenshot(region=region)
        haystack = cv2.cvtColor(np.array(capture), cv2.COLOR_RGB2BGR)
        needle = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if needle is None:
            raise FileNotFoundError(f"Image introuvable : {template_path}")

        result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
        _min_v, max_v, _min_l, max_loc = cv2.minMaxLoc(result)
        if max_v < confidence:
            return None
        h, w = needle.shape[:2]
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        if region:
            cx += region[0]
            cy += region[1]
        return int(cx), int(cy)
