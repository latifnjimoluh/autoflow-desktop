"""``ThemeManager`` — applique et bascule le thème à chaud (source unique).

Le gestionnaire :

1. charge les **tokens** du thème courant (clair/sombre),
2. **génère le QSS** correspondant et l'applique à toute la ``QApplication``,
3. le **ré-applique à la volée** lors d'une bascule (``set_theme`` / ``toggle``),
4. émet ``theme_changed`` pour que les vues peintes à la main (toile à nœuds…)
   se rafraîchissent.

Il expose aussi des helpers purs (``tokens()``, ``current``) utilisables hors
écran. Un **singleton** (:func:`manager`) sert de point d'accès global et
alimente les shims rétro-compatibles de ``autoflow/gui/theme.py``.
"""

from __future__ import annotations

from typing import Any

from . import tokens as _tokens
from .fonts import load_embedded_fonts
from .qss import build_qss

# QSS pré-généré par thème (les tokens ne changent pas à l'exécution).
_QSS_CACHE: dict[str, str] = {}


def qss_for(theme: str) -> str:
    """Renvoie (en cache) le QSS complet pour ``theme``."""
    if theme not in _tokens.THEMES:
        theme = "dark"
    if theme not in _QSS_CACHE:
        _QSS_CACHE[theme] = build_qss(_tokens.resolve(theme))
    return _QSS_CACHE[theme]


def _qobject_base():
    """Renvoie la base ``QObject`` + le type ``Signal`` (ou des stubs hors Qt)."""
    try:
        from PySide6.QtCore import QObject, Signal
        return QObject, Signal
    except Exception:  # noqa: BLE001
        class _Stub:  # pragma: no cover - chemin sans Qt
            def __init__(self, *a, **k):
                pass

        def _signal(*_a, **_k):  # pragma: no cover
            return None
        return _Stub, _signal


_QObject, _Signal = _qobject_base()


class ThemeManager(_QObject):
    """Gestionnaire central de thème, branché sur une ``QApplication``."""

    # Émis après chaque (ré)application : porte le nom du thème courant.
    theme_changed = _Signal(str) if callable(_Signal) else None

    def __init__(self, app: Any | None = None, theme: str = "dark") -> None:
        super().__init__()
        self._app = app
        self._theme = theme if theme in _tokens.THEMES else "dark"

    # -- État ----------------------------------------------------------
    @property
    def current(self) -> str:
        """Nom du thème courant (``dark`` / ``light``)."""
        return self._theme

    def tokens(self) -> dict[str, str]:
        """Dictionnaire plat de tokens du thème courant."""
        return _tokens.resolve(self._theme)

    # -- Application ---------------------------------------------------
    def attach(self, app: Any) -> None:
        """Associe une ``QApplication`` et applique le thème courant."""
        self._app = app
        load_embedded_fonts()
        self.apply()

    def apply(self, theme: str | None = None) -> None:
        """Applique ``theme`` (ou le thème courant) à l'application."""
        if theme is not None and theme in _tokens.THEMES:
            self._theme = theme
        if self._app is not None:
            self._app.setStyleSheet(qss_for(self._theme))
        if self.theme_changed is not None:
            try:
                self.theme_changed.emit(self._theme)
            except Exception:  # noqa: BLE001 — émission sûre même sans boucle Qt
                pass

    def set_theme(self, theme: str) -> None:
        """Bascule vers ``theme`` et ré-applique le style à chaud."""
        self.apply(theme)

    def toggle(self) -> str:
        """Alterne clair ⇄ sombre, ré-applique, et renvoie le nouveau thème."""
        self.apply("light" if self._theme == "dark" else "dark")
        return self._theme


# --- Singleton global ----------------------------------------------------
_INSTANCE: ThemeManager | None = None


def manager() -> ThemeManager:
    """Renvoie le ``ThemeManager`` global (créé à la demande)."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ThemeManager()
    return _INSTANCE
