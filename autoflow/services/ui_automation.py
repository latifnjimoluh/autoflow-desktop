"""Ciblage d'éléments d'interface Windows (UI Automation) — **paresseux/mockable**.

S'appuie sur ``pywinauto`` (back-end UIA) **importé à l'usage**. Sur les systèmes
sans support, les fonctions lèvent :class:`UiAutomationUnavailable` (capturée par
l'action, qui dégrade proprement). Un *backend* injectable rend l'ensemble
testable sans environnement Windows réel.
"""

from __future__ import annotations

import sys
from typing import Any


class UiAutomationUnavailable(RuntimeError):
    """Le ciblage d'éléments d'interface n'est pas disponible sur ce système."""


def is_available(backend: Any = None) -> bool:
    """Indique si le ciblage UI est disponible (Windows + pywinauto)."""
    if backend is not None:
        return True
    if not sys.platform.startswith("win"):
        return False
    try:  # pragma: no cover - dépend de l'environnement Windows
        import pywinauto  # noqa: F401
        return True
    except ImportError:
        return False


def _connect(window_title: str, backend: Any = None):
    """Renvoie la fenêtre racine pour ``window_title`` (ou via ``backend``)."""
    if backend is not None:
        return backend.window(window_title)
    if not sys.platform.startswith("win"):
        raise UiAutomationUnavailable("Ciblage UI : Windows requis.")
    try:  # pragma: no cover
        from pywinauto import Desktop
        return Desktop(backend="uia").window(title_re=f".*{window_title}.*")
    except ImportError as exc:  # pragma: no cover
        raise UiAutomationUnavailable("« pywinauto » n'est pas installé.") from exc


def click_element(window_title: str, name: str, control_type: str = "",
                  backend: Any = None) -> bool:
    """Clique sur un élément désigné par son nom (et type optionnel)."""
    window = _connect(window_title, backend)
    element = _find(window, name, control_type)
    element.click_input()
    return True


def set_text(window_title: str, name: str, text: str, control_type: str = "",
             backend: Any = None) -> bool:
    """Saisit ``text`` dans un champ désigné par son nom."""
    window = _connect(window_title, backend)
    element = _find(window, name, control_type)
    element.set_text(text)
    return True


def _find(window: Any, name: str, control_type: str):
    """Localise un élément enfant par nom/type (API pywinauto-like)."""
    if control_type:
        return window.child_window(title=name, control_type=control_type)
    return window.child_window(title=name)
