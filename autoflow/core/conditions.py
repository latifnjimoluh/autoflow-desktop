"""Évaluation des tests partagés par les actions de contrôle de flux.

Utilisé par l'action conditionnelle (``condition``) et les boucles
conditionnelles (``loop`` en mode *while*/*until*).
"""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Any

# Types de tests proposés à l'utilisateur (valeur -> libellé FR).
CONDITION_TESTS = {
    "window_present": "Fenêtre présente",
    "window_absent": "Fenêtre absente",
    "image_present": "Image présente à l'écran",
    "pixel_color": "Couleur d'un pixel",
    "file_exists": "Fichier existant",
    "variable_compare": "Comparaison de variable",
}

_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


def evaluate(params: dict[str, Any], inputs: Any, windows: Any,
             context: dict[str, Any]) -> bool:
    """Évalue un test et renvoie ``True`` ou ``False``.

    ``params`` contient au moins ``test`` plus les champs propres au test.
    """
    test = params.get("test", "window_present")
    store = (context or {}).get("variables")

    def resolve(value: Any) -> Any:
        return store.resolve(value) if (store is not None and isinstance(value, str)) else value

    if test == "window_present":
        return bool(windows.find_windows(resolve(params.get("title", "")),
                                         params.get("match", "contains")))
    if test == "window_absent":
        return not windows.find_windows(resolve(params.get("title", "")),
                                        params.get("match", "contains"))
    if test == "image_present":
        return _image_present(params, inputs, context, resolve)
    if test == "pixel_color":
        return _pixel_matches(params, inputs)
    if test == "file_exists":
        return Path(str(resolve(params.get("file_path", "")))).exists()
    if test == "variable_compare":
        return _compare_variable(params, store, resolve)
    raise ValueError(f"Test de condition inconnu : {test!r}")


def _image_present(params, inputs, context, resolve) -> bool:
    path = str(resolve(params.get("image_path", "")))
    confidence = float(params.get("confidence", 0.8))
    vision = (context or {}).get("vision")
    if vision is not None and vision.is_available():
        return vision.locate_center(path, confidence=confidence) is not None
    # Repli sur pyautogui si OpenCV indisponible.
    return inputs.locate_center(path, confidence=confidence) is not None


def _pixel_matches(params, inputs) -> bool:
    x = int(params.get("x", 0))
    y = int(params.get("y", 0))
    target = _parse_color(params.get("color", "#000000"))
    tolerance = int(params.get("tolerance", 10))
    actual = inputs.pixel(x, y)
    return all(abs(a - b) <= tolerance for a, b in zip(actual, target, strict=False))


def _compare_variable(params, store, resolve) -> bool:
    if store is None:
        return False
    name = params.get("var_name", "")
    op = _OPERATORS.get(params.get("operator", "=="))
    if op is None:
        if params.get("operator") == "contains":
            return str(resolve(params.get("value", ""))) in str(store.get(name, ""))
        raise ValueError(f"Opérateur inconnu : {params.get('operator')!r}")
    left = store.get(name)
    right = resolve(params.get("value", ""))
    left, right = _coerce(left, right)
    return op(left, right)


def _coerce(left: Any, right: Any) -> tuple[Any, Any]:
    """Tente une comparaison numérique, sinon compare en chaînes."""
    try:
        return float(left), float(right)
    except (TypeError, ValueError):
        return str(left), str(right)


def _parse_color(value: Any) -> tuple[int, int, int]:
    """Convertit « #RRGGBB » ou « r,g,b » en triplet (r, g, b)."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(int(c) for c in value)  # type: ignore[return-value]
    text = str(value).strip().lstrip("#")
    if "," in text:
        parts = [int(p) for p in text.split(",")]
        return parts[0], parts[1], parts[2]
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
