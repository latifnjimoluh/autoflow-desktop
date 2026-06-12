"""Capture et normalisation des touches du clavier.

Fournit :

- une **table de correspondance** ``pynput`` → noms attendus par le backend
  (``pyautogui``), pour la capture en direct d'une touche / d'un raccourci ;
- un **catalogue cherchable** de toutes les touches (lettres, chiffres, F1–F24,
  flèches, navigation, média…) pour la liste déroulante ;
- des aides d'affichage (« Ctrl + Maj + S »).

La logique est **pure** (aucun import lié à l'écran au niveau module), donc
testable sans clavier ni affichage : les tests fournissent de faux objets de
touche imitant ``pynput``.
"""

from __future__ import annotations

from typing import Any

# Modificateurs reconnus, dans l'ordre d'affichage canonique.
MODIFIERS = ("ctrl", "alt", "shift", "win")

# Libellés FR des modificateurs (affichage en badges).
MODIFIER_LABELS = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Maj",
    "win": "Win",
}

# Correspondance des noms ``pynput`` (Key.<name>) vers les noms ``pyautogui``.
_PYNPUT_SPECIAL = {
    "alt": "alt", "alt_l": "alt", "alt_r": "altright", "alt_gr": "altright",
    "ctrl": "ctrl", "ctrl_l": "ctrl", "ctrl_r": "ctrlright",
    "shift": "shift", "shift_l": "shift", "shift_r": "shiftright",
    "cmd": "win", "cmd_l": "win", "cmd_r": "win",
    "enter": "enter", "return": "enter",
    "space": "space", "tab": "tab", "esc": "esc", "escape": "esc",
    "backspace": "backspace", "delete": "delete", "insert": "insert",
    "home": "home", "end": "end", "page_up": "pageup", "page_down": "pagedown",
    "up": "up", "down": "down", "left": "left", "right": "right",
    "caps_lock": "capslock", "num_lock": "numlock", "scroll_lock": "scrolllock",
    "print_screen": "printscreen", "pause": "pause", "menu": "apps",
    "media_play_pause": "playpause", "media_volume_mute": "volumemute",
    "media_volume_up": "volumeup", "media_volume_down": "volumedown",
    "media_next": "nexttrack", "media_previous": "prevtrack",
}

# Catalogue cherchable, regroupé par catégorie (valeur backend -> libellé FR).
KEY_CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "Lettres": [(c, c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"],
    "Chiffres": [(str(n), str(n)) for n in range(10)],
    "Fonction": [(f"f{n}", f"F{n}") for n in range(1, 25)],
    "Navigation": [
        ("up", "Flèche haut"), ("down", "Flèche bas"),
        ("left", "Flèche gauche"), ("right", "Flèche droite"),
        ("home", "Début"), ("end", "Fin"),
        ("pageup", "Page haut"), ("pagedown", "Page bas"),
    ],
    "Édition": [
        ("enter", "Entrée"), ("tab", "Tab"), ("space", "Espace"),
        ("backspace", "Retour arrière"), ("delete", "Suppr"),
        ("insert", "Inser"), ("esc", "Échap"),
    ],
    "Verrous": [
        ("capslock", "Verr. Maj"), ("numlock", "Verr. Num"),
        ("scrolllock", "Arrêt défil."),
    ],
    "Système": [
        ("printscreen", "Impr. écran"), ("pause", "Pause"), ("apps", "Menu contextuel"),
    ],
    "Média": [
        ("playpause", "Lecture / Pause"), ("nexttrack", "Piste suivante"),
        ("prevtrack", "Piste précédente"), ("volumemute", "Muet"),
        ("volumeup", "Volume +"), ("volumedown", "Volume -"),
    ],
    "Symboles": [
        (",", "Virgule ,"), (".", "Point ."), ("/", "Slash /"),
        (";", "Point-virgule ;"), ("'", "Apostrophe '"), ("-", "Tiret -"),
        ("=", "Égal ="), ("[", "Crochet ["), ("]", "Crochet ]"),
    ],
}

# Liste plate de toutes les touches (valeur backend -> libellé), pour recherche.
ALL_KEYS: list[tuple[str, str]] = [
    item for items in KEY_CATEGORIES.values() for item in items
]


def normalize_key(name: Any) -> str:
    """Normalise un nom de touche libre vers le nom attendu par le backend.

    Tolère les saisies courantes (« Entrée », « ESC », « Ctrl »…). Renvoie une
    chaîne minuscule sans espaces superflus.
    """
    text = str(name or "").strip().lower()
    aliases = {
        "entrée": "enter", "entree": "enter", "retour": "enter",
        "échap": "esc", "echap": "esc", "escape": "esc",
        "espace": "space", "tabulation": "tab",
        "suppr": "delete", "supprimer": "delete",
        "retour arrière": "backspace", "retour arriere": "backspace",
        "début": "home", "debut": "home", "fin": "end",
        "haut": "up", "bas": "down", "gauche": "left", "droite": "right",
        "ctrl": "ctrl", "contrôle": "ctrl", "controle": "ctrl",
        "maj": "shift", "majuscule": "shift",
        "windows": "win", "cmd": "win", "commande": "win",
    }
    return aliases.get(text, text)


def pynput_to_name(key: Any) -> str:
    """Convertit un objet touche ``pynput`` en nom backend (``pyautogui``).

    Accepte aussi bien ``KeyCode`` (touche de caractère, attribut ``char``) que
    ``Key`` (touche spéciale, attribut ``name``). Les tests passent de faux
    objets exposant ces attributs.
    """
    # Touche de caractère : KeyCode.char
    char = getattr(key, "char", None)
    if char:
        return str(char).lower()
    # Touche spéciale : Key.name (ex. "ctrl_l", "f5", "space")
    name = getattr(key, "name", None)
    if name:
        lowered = str(name).lower()
        return _PYNPUT_SPECIAL.get(lowered, lowered)
    # Repli : représentation textuelle nettoyée.
    return normalize_key(str(key).replace("Key.", ""))


def is_modifier(key_name: str) -> bool:
    """Indique si ``key_name`` (déjà normalisé) est un modificateur."""
    base = key_name.replace("right", "")
    return base in MODIFIERS


def combo_to_keys(modifiers: list[str], final_key: str) -> list[str]:
    """Assemble une combinaison ``modificateurs + touche`` ordonnée et nettoyée.

    Args:
        modifiers : sous-ensemble de :data:`MODIFIERS`.
        final_key : touche finale (sera normalisée).
    """
    ordered = [m for m in MODIFIERS if m in set(modifiers)]
    final = normalize_key(final_key)
    keys = list(ordered)
    if final and final not in keys:
        keys.append(final)
    return keys


# Libellés FR conviviaux par touche (backend -> libellé), pour l'affichage.
_DISPLAY_LABELS = {backend: label for backend, label in ALL_KEYS}
_DISPLAY_LABELS.update(MODIFIER_LABELS)


def key_label(key: Any) -> str:
    """Rend une touche unique en libellé convivial FR (« Entrée », « Ctrl »…)."""
    norm = normalize_key(key)
    if norm in _DISPLAY_LABELS:
        return _DISPLAY_LABELS[norm]
    return norm.upper() if len(norm) == 1 else norm.capitalize()


def keys_to_label(keys: Any) -> str:
    """Rend une combinaison de touches en libellé lisible « Ctrl + Maj + S »."""
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.replace(",", "+").split("+") if k.strip()]
    return " + ".join(key_label(key) for key in (keys or []))
