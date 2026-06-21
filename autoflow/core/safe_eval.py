"""Évaluateur d'expressions arithmétiques **restreint** (sans ``eval`` brut).

Analyse l'expression en AST et n'autorise que des nombres, les opérateurs
arithmétiques, quelques fonctions mathématiques sûres et des variables fournies.
Toute construction non autorisée lève :class:`ValueError`. Aucune exécution de
code arbitraire n'est possible (pas d'accès aux attributs, appels libres, etc.).
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable
from typing import Any

_BINOPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY: dict[type, Callable[[Any], Any]] = {
    ast.UAdd: operator.pos, ast.USub: operator.neg}

_FUNCS: dict[str, Callable[..., Any]] = {
    "abs": abs, "round": round, "min": min, "max": max,
    "int": int, "float": float, "sqrt": math.sqrt,
    "floor": math.floor, "ceil": math.ceil, "pow": pow,
}
_CONSTS = {"pi": math.pi, "e": math.e}


def evaluate(expression: str, variables: dict[str, Any] | None = None) -> float | int:
    """Évalue une expression arithmétique restreinte et renvoie un nombre.

    ``variables`` fournit des valeurs nommées (converties en nombres). Lève
    :class:`ValueError` si l'expression est invalide ou non autorisée.
    """
    env = dict(_CONSTS)
    for key, value in (variables or {}).items():
        try:
            num = float(value)
            env[str(key)] = int(num) if num.is_integer() else num
        except (TypeError, ValueError):
            continue  # variables non numériques ignorées
    try:
        tree = ast.parse(str(expression), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Expression invalide : {exc.msg}") from exc
    result = _eval(tree.body, env)
    return result


def _eval(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Seules les valeurs numériques sont autorisées.")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"Variable inconnue : {node.id!r}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand, env))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func = _FUNCS.get(node.func.id)
        if func is None:
            raise ValueError(f"Fonction non autorisée : {node.func.id!r}")
        args = [_eval(a, env) for a in node.args]
        return func(*args)
    raise ValueError("Construction non autorisée dans l'expression.")
