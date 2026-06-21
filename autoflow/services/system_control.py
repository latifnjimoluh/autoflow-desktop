"""Contrôle système : volume, verrouillage, veille, arrêt/redémarrage, écrans.

Fonctions propres à Windows via ``ctypes``/commandes système, en **import
paresseux** et avec **dégradation propre** sur les autres OS (renvoie ``False``
+ message, jamais de crash). Toutes les fonctions acceptent un *runner*
injectable pour les tests (aucun test n'éteint réellement la machine !).
"""

from __future__ import annotations

import sys
from collections.abc import Callable

Runner = Callable[[list[str]], int]


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _run(cmd: list[str], runner: Runner | None) -> bool:
    if runner is not None:
        return int(runner(cmd)) == 0
    import subprocess
    return subprocess.run(cmd, check=False).returncode == 0


def lock_session(runner: Runner | None = None) -> bool:
    """Verrouille la session (Windows : rundll32 user32)."""
    if not is_windows():
        return False
    return _run(["rundll32.exe", "user32.dll,LockWorkStation"], runner)


def sleep_machine(runner: Runner | None = None) -> bool:
    """Met l'ordinateur en veille (Windows)."""
    if not is_windows():
        return False
    return _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], runner)


def shutdown(restart: bool = False, delay: int = 5, runner: Runner | None = None) -> bool:
    """Éteint ou redémarre (Windows : ``shutdown``). Appel **toujours confirmé**
    en amont par l'action (jamais silencieux)."""
    if not is_windows():
        return False
    flag = "/r" if restart else "/s"
    return _run(["shutdown", flag, "/t", str(int(delay))], runner)


def set_volume(level: int, controller=None) -> bool:
    """Règle le volume principal (0–100). ``controller`` injectable (test).

    Utilise ``pycaw`` si disponible ; sinon dégradation propre (``False``).
    """
    level = max(0, min(100, int(level)))
    if controller is not None:
        controller(level)
        return True
    if not is_windows():
        return False
    try:  # pragma: no cover - dépend de pycaw/Windows
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return True
    except Exception:  # noqa: BLE001
        return False


def mute(controller=None) -> bool:
    """Coupe le son (volume à 0)."""
    return set_volume(0, controller=controller)


def list_monitors(provider=None) -> list[dict]:
    """Renvoie la liste des moniteurs ``[{index, x, y, width, height}]``.

    ``provider`` injectable (test). Utilise l'API d'écran de Qt si disponible.
    """
    if provider is not None:
        return provider()
    try:
        from PySide6.QtGui import QGuiApplication
        app = QGuiApplication.instance()
        if app is None:  # pragma: no cover - nécessite une QApplication
            return []
        result = []
        for i, screen in enumerate(QGuiApplication.screens()):
            geo = screen.geometry()
            result.append({"index": i, "x": geo.x(), "y": geo.y(),
                           "width": geo.width(), "height": geo.height()})
        return result
    except Exception:  # noqa: BLE001
        return []
