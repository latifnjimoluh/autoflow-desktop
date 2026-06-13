"""Façade d'entrées souris/clavier autour de ``pyautogui``.

`pyautogui` n'est **jamais** importé au niveau module : il l'est paresseusement
à la première utilisation. Les tests peuvent ainsi importer ce module sans
écran, et mocker entièrement la classe :class:`InputBackend`.
"""

from __future__ import annotations

from typing import Any


class InputBackend:
    """Encapsule les opérations souris/clavier et la capture d'écran.

    Toutes les méthodes délèguent à ``pyautogui`` chargé à la demande. En
    environnement sans affichage, l'import n'a lieu qu'à l'exécution réelle.
    """

    def __init__(self, failsafe: bool = True, pause: float = 0.05) -> None:
        self._failsafe = failsafe
        self._pause = pause
        self._pg: Any = None

    # -- Chargement paresseux ---------------------------------------------
    def _pyautogui(self) -> Any:
        """Importe et configure ``pyautogui`` à la première utilisation."""
        if self._pg is None:
            import pyautogui  # import paresseux volontaire

            pyautogui.FAILSAFE = self._failsafe
            pyautogui.PAUSE = self._pause
            self._pg = pyautogui
        return self._pg

    # -- Réglages ----------------------------------------------------------
    def set_failsafe(self, enabled: bool) -> None:
        """Active/désactive le failsafe (souris coin haut-gauche = arrêt)."""
        self._failsafe = enabled
        if self._pg is not None:
            self._pg.FAILSAFE = enabled

    def set_pause(self, pause: float) -> None:
        """Règle la pause globale appliquée par pyautogui après chaque appel."""
        self._pause = pause
        if self._pg is not None:
            self._pg.PAUSE = pause

    # -- Souris ------------------------------------------------------------
    def click(self, x: int | None = None, y: int | None = None,
              button: str = "left", clicks: int = 1) -> None:
        """Clique aux coordonnées données (ou à la position actuelle si None)."""
        pg = self._pyautogui()
        if x is None or y is None:
            pg.click(button=button, clicks=clicks)
        else:
            pg.click(x=x, y=y, button=button, clicks=clicks)

    def move_to(self, x: int, y: int, duration: float = 0.0) -> None:
        """Déplace le curseur vers (x, y)."""
        self._pyautogui().moveTo(x, y, duration=duration)

    def drag_to(self, x1: int, y1: int, x2: int, y2: int,
                duration: float = 0.5, button: str = "left") -> None:
        """Glisse de (x1, y1) vers (x2, y2)."""
        pg = self._pyautogui()
        pg.moveTo(x1, y1)
        pg.dragTo(x2, y2, duration=duration, button=button)

    def scroll(self, amount: int) -> None:
        """Fait défiler de ``amount`` crans (positif = haut)."""
        self._pyautogui().scroll(amount)

    def position(self) -> tuple[int, int]:
        """Renvoie la position actuelle du curseur."""
        pos = self._pyautogui().position()
        return int(pos[0]), int(pos[1])

    def size(self) -> tuple[int, int]:
        """Renvoie la taille de l'écran principal (largeur, hauteur)."""
        size = self._pyautogui().size()
        return int(size[0]), int(size[1])

    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        """Renvoie la couleur (r, g, b) du pixel aux coordonnées données."""
        color = self._pyautogui().pixel(int(x), int(y))
        return int(color[0]), int(color[1]), int(color[2])

    # -- Clavier -----------------------------------------------------------
    def press(self, key: str, presses: int = 1, interval: float = 0.0) -> None:
        """Appuie ``presses`` fois sur la touche ``key``."""
        self._pyautogui().press(key, presses=presses, interval=interval)

    def hotkey(self, keys: list[str]) -> None:
        """Appuie sur une combinaison de touches simultanément."""
        self._pyautogui().hotkey(*keys)

    def type_text(self, text: str, interval: float = 0.0) -> None:
        """Tape une chaîne de caractères."""
        self._pyautogui().typewrite(text, interval=interval)

    # -- Écran -------------------------------------------------------------
    def screenshot(self, path: str, region: tuple[int, int, int, int] | None = None) -> str:
        """Capture l'écran (ou une région) et l'enregistre dans ``path``."""
        pg = self._pyautogui()
        image = pg.screenshot(region=region) if region else pg.screenshot()
        image.save(path)
        return path

    def locate_center(self, image_path: str, confidence: float = 0.9) -> tuple[int, int] | None:
        """Localise une image à l'écran et renvoie le centre, ou None."""
        pg = self._pyautogui()
        try:
            point = pg.locateCenterOnScreen(image_path, confidence=confidence)
        except TypeError:
            # ``confidence`` requiert OpenCV ; repli sans ce paramètre.
            point = pg.locateCenterOnScreen(image_path)
        if point is None:
            return None
        return int(point[0]), int(point[1])
