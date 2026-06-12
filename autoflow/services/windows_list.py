"""Énumération des fenêtres actuellement ouvertes (titre + handle).

Alimente le sélecteur de fenêtres concret : plutôt que de taper un titre à
l'aveugle, l'utilisateur choisit dans la liste des fenêtres réellement ouvertes.

``pygetwindow`` est importé **paresseusement** ; un fournisseur (``gw_provider``)
peut être injecté pour les tests, ce qui rend la fonction testable sans écran.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class WindowInfo:
    """Description légère d'une fenêtre ouverte."""

    title: str
    handle: int = 0
    app: str = ""

    def __str__(self) -> str:  # pragma: no cover - confort d'affichage
        return self.title


def _default_gw() -> Any:
    """Importe ``pygetwindow`` paresseusement."""
    import pygetwindow  # import paresseux volontaire

    return pygetwindow


def list_open_windows(
    gw_provider: Callable[[], Any] | None = None,
    *,
    include_empty: bool = False,
) -> list[WindowInfo]:
    """Renvoie la liste des fenêtres ouvertes, triée et dédupliquée par titre.

    Args:
        gw_provider : fournisseur de module ``pygetwindow`` (injectable pour les
            tests). Par défaut, importe la vraie bibliothèque.
        include_empty : si ``False`` (défaut), ignore les fenêtres sans titre.

    Renvoie une liste vide en cas d'erreur (pas d'affichage, lib absente…), de
    sorte que l'appelant n'a jamais à gérer d'exception.
    """
    provider = gw_provider or _default_gw
    try:
        gw = provider()
        raw = gw.getAllWindows()
    except Exception:  # noqa: BLE001 - pas d'affichage / lib absente
        return []

    seen: set[str] = set()
    results: list[WindowInfo] = []
    for window in raw:
        title = (getattr(window, "title", "") or "").strip()
        if not title and not include_empty:
            continue
        if title in seen:
            continue
        seen.add(title)
        handle = getattr(window, "_hWnd", None)
        results.append(WindowInfo(title=title, handle=int(handle or 0)))
    results.sort(key=lambda w: w.title.lower())
    return results


def window_titles(gw_provider: Callable[[], Any] | None = None) -> list[str]:
    """Raccourci : renvoie uniquement les titres des fenêtres ouvertes."""
    return [w.title for w in list_open_windows(gw_provider)]
