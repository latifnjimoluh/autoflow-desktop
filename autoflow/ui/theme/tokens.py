"""Tokens de design — **source unique de vérité** du système visuel AutoFlow.

Aucune couleur, taille, rayon ou ombre n'est codé en dur ailleurs dans l'app :
tout dérive de ce module. Deux thèmes complets (``dark`` / ``light``) partagent
le même langage visuel (accent, sémantiques, typographie, espacement, rayons,
élévation) et ne diffèrent que par leurs **surfaces** et **textes**.

Direction artistique : moderne, calme et arrondie — à mi-chemin entre la toile
à nœuds conviviale de n8n et le minimalisme de Linear/Raycast. Une **seule**
couleur d'accent affirmée (indigo ``#6D5EF0``), profondeur subtile, lisibilité
avant tout.

API principale :

- :data:`THEMES` — la liste des thèmes disponibles.
- :func:`resolve` — renvoie un **dictionnaire plat** ``{token: valeur}`` pour un
  thème, prêt à être injecté dans le QSS. Inclut des alias rétro-compatibles
  avec l'ancienne palette (``window``, ``accent_pressed``, ``danger``…).
- :data:`REQUIRED_TOKENS` — l'ensemble des clés garanties pour **chaque** thème
  (vérifié par les tests de cohérence).
"""

from __future__ import annotations

THEMES = ("dark", "light")

# --- Couleur d'accent (partagée par les deux thèmes) ---------------------
# Une seule couleur d'accent affirmée : indigo/violet, avec ses états.
ACCENT = {
    "accent": "#6D5EF0",
    "accent_hover": "#5B4EE0",
    "accent_active": "#4E42C9",
    "accent_subtle": "#8B7FF3",   # variante claire (texte d'accent sur surface)
    "accent_2": "#14B8A6",        # accent secondaire (teal) — surbrillances
    "on_accent": "#FFFFFF",       # texte/icône posé sur l'accent
}

# --- Couleurs sémantiques (jamais utilisées seules — voir §accessibilité) -
SEMANTIC = {
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
}

# --- Surfaces & textes propres à chaque thème ----------------------------
_DARK_SURFACES = {
    "bg": "#0E0F13",            # fond général de l'application
    "surface": "#16181F",       # panneaux, cartes
    "surface_alt": "#1E212B",   # champs, éléments, surface alternée
    "elevated": "#1E212B",      # surface surélevée (menus, popups, survol)
    "overlay": "#11131A",       # voile de fond des dialogues
    "border": "#2A2E3A",
    "border_strong": "#3A3F4D",
    "text": "#ECEDEF",
    "text_secondary": "#A0A4AE",
    "muted": "#6B7280",
    "selection": "#2D2A55",     # accent désaturé pour la sélection de texte
    "scrim": "rgba(8, 9, 12, 0.55)",
}

_LIGHT_SURFACES = {
    "bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "surface_alt": "#F1F2F5",
    "elevated": "#FFFFFF",
    "overlay": "#E7E9EF",
    "border": "#E3E5EA",
    "border_strong": "#C9CDD6",
    "text": "#1A1C22",
    "text_secondary": "#5A5F6B",
    "muted": "#8A8F9A",
    "selection": "#E5E2FB",
    "scrim": "rgba(20, 22, 30, 0.35)",
}

_SURFACES = {"dark": _DARK_SURFACES, "light": _LIGHT_SURFACES}

# --- Typographie ----------------------------------------------------------
# Polices embarquées si présentes (voir fonts/), repli système robuste.
FONT_SANS = '"Inter", "Segoe UI", system-ui, "Roboto", sans-serif'
FONT_MONO = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'

# Échelle typographique : (taille px, poids). Interligne ~1.4–1.5.
TYPE_SCALE = {
    "display": (24, 600),
    "title": (20, 600),
    "subtitle": (16, 600),
    "body": (14, 400),
    "label": (12, 500),
    "caption": (11, 400),
    "mono": (13, 400),
}

# --- Espacement (base 8), rayons, élévation ------------------------------
SPACING = {
    "xxs": 2, "xs": 4, "sm": 8, "md": 12,
    "lg": 16, "xl": 24, "2xl": 32, "3xl": 48,
}

RADIUS = {"sm": 6, "md": 10, "lg": 14, "pill": 999}

# Trois niveaux d'élévation (rayon de flou, alpha, décalage vertical).
# Qt n'a pas de box-shadow : appliqués via QGraphicsDropShadowEffect.
ELEVATION = {
    1: {"blur": 12, "alpha": 38, "dy": 2},
    2: {"blur": 24, "alpha": 55, "dy": 6},
    3: {"blur": 40, "alpha": 70, "dy": 12},
}

# --- Couleurs de catégorie d'action (liserés de nœuds) -------------------
# Cohérentes entre thèmes ; teintes lisibles sur surface claire et sombre.
CATEGORY_COLORS = {
    "Clavier": "#6D5EF0",
    "Souris": "#14B8A6",
    "Fenêtres": "#3B82F6",
    "Système": "#F59E0B",
    "Contrôle": "#EC4899",
    "Variables": "#8B5CF6",
    "Écran": "#06B6D4",
    "Général": "#6B7280",
}


def _flatten(theme: str) -> dict[str, str]:
    """Assemble le dictionnaire plat de tokens pour ``theme``."""
    if theme not in _SURFACES:
        theme = "dark"
    flat: dict[str, str] = {}
    flat.update(ACCENT)
    flat.update(SEMANTIC)
    flat.update(_SURFACES[theme])
    flat["font_sans"] = FONT_SANS
    flat["font_mono"] = FONT_MONO

    # --- Alias rétro-compatibles avec l'ancienne palette gui/theme.py ----
    flat["window"] = flat["bg"]
    flat["accent_text"] = flat["on_accent"]
    flat["accent_pressed"] = flat["accent_active"]
    flat["danger"] = flat["error"]
    return flat


# Ensemble des clés garanties pour chaque thème (contrat testé).
REQUIRED_TOKENS = frozenset(_flatten("dark"))


def resolve(theme: str = "dark") -> dict[str, str]:
    """Renvoie le dictionnaire plat ``{token: valeur}`` pour ``theme``."""
    return _flatten(theme)


def category_color(category: str) -> str:
    """Couleur de liseré associée à une catégorie d'action (repli neutre)."""
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["Général"])
