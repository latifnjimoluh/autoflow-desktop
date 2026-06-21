"""Gestion des fenêtres : ciblage par titre et passage au premier plan.

Ce module isole les dépendances spécifiques (``pygetwindow``, ``ctypes``) et
les importe **paresseusement**. Il intègre la technique Windows essentielle des
scripts d'origine pour vaincre le « Access Denied » de ``SetForegroundWindow``
en simulant un appui sur Alt, ainsi que la neutralisation du faux
« Error code 0 » remonté par ``pygetwindow`` lors d'une activation réussie.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

SW_RESTORE = 9
_VK_MENU = 0x12  # touche Alt
_KEYEVENTF_KEYUP = 0x0002


def force_foreground_window(hwnd: int) -> None:
    """Force une fenêtre Windows au premier plan (technique des scripts d'origine).

    Contourne le « Access Denied » de ``SetForegroundWindow`` en simulant un
    appui/relâchement de la touche Alt, restaure la fenêtre si minimisée, puis
    la place au premier plan. Sans effet hors Windows.
    """
    if not sys.platform.startswith("win"):
        return
    import ctypes

    user32 = ctypes.windll.user32
    user32.keybd_event(_VK_MENU, 0, 0, 0)               # Alt enfoncée
    user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)  # Alt relâchée
    user32.ShowWindow(hwnd, SW_RESTORE)                 # restaure si minimisé
    user32.SetForegroundWindow(hwnd)


def _get_gw() -> Any:
    """Importe ``pygetwindow`` paresseusement (mockable dans les tests)."""
    import pygetwindow  # import paresseux volontaire

    return pygetwindow


def _matches(title: str, target: str, match: str) -> bool:
    """Indique si ``title`` correspond à ``target`` selon le mode ``match``."""
    if match == "exact":
        return title == target
    return target.lower() in (title or "").lower()


class WindowsBackend:
    """Façade de gestion des fenêtres, mockable et tolérante hors Windows."""

    def __init__(self) -> None:
        self.is_windows = sys.platform.startswith("win")

    # -- Recherche ---------------------------------------------------------
    def find_windows(self, title: str, match: str = "contains") -> list[Any]:
        """Renvoie la liste des fenêtres dont le titre correspond."""
        gw = _get_gw()
        results = []
        for window in gw.getAllWindows():
            win_title = getattr(window, "title", "") or ""
            if win_title and _matches(win_title, title, match):
                results.append(window)
        return results

    # -- Activation --------------------------------------------------------
    def activate(self, title: str, match: str = "contains",
                 force_foreground: bool = False) -> bool:
        """Active la première fenêtre correspondante ; renvoie ``True`` si trouvée.

        Neutralise le faux « Error code 0 » de ``pygetwindow`` (qui signifie en
        réalité « opération réussie ») et applique éventuellement la technique
        ctypes de premier plan forcé.
        """
        windows = self.find_windows(title, match)
        if not windows:
            return False
        window = windows[0]
        try:
            window.activate()
        except Exception as exc:  # noqa: BLE001 - on filtre le faux positif
            if not _is_benign_error(exc):
                raise
        if force_foreground:
            hwnd = getattr(window, "_hWnd", None)
            if hwnd is not None:
                force_foreground_window(hwnd)
        return True

    # -- Attente -----------------------------------------------------------
    def wait_for_window(self, title: str, match: str = "contains",
                        timeout: float = 10.0,
                        sleep: Callable[[float], None] | None = None) -> bool:
        """Attend l'apparition d'une fenêtre correspondante (avec timeout)."""
        if sleep is None:
            import time

            sleep = time.sleep
        elapsed = 0.0
        step = 0.5
        while elapsed <= timeout:
            if self.find_windows(title, match):
                return True
            sleep(step)
            elapsed += step
        return False

    # -- Lancement ---------------------------------------------------------
    def launch(self, path: str, args: list[str] | None = None) -> Any:
        """Lance un exécutable (avec arguments) ou ouvre un fichier."""
        args = args or []
        if args:
            import subprocess

            return subprocess.Popen([path, *args])
        # Sans argument : privilégie l'association de fichier sous Windows.
        if self.is_windows and not args:
            import os

            try:
                os.startfile(path)  # type: ignore[attr-defined]
                return None
            except (AttributeError, OSError):
                pass
        import subprocess

        return subprocess.Popen([path])


def _is_benign_error(exc: Exception) -> bool:
    """Détecte le faux échec « Error code 0 » (= succès) de pygetwindow."""
    message = str(exc).lower()
    return "0" in message and ("error code" in message or "code from windows" in message)
