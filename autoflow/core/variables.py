"""Magasin de variables d'exécution et substitution de gabarits ``{{var}}``.

Chaque exécution dispose de son propre :class:`VariableStore`. Les actions
peuvent y définir/lire des variables et réutiliser leurs valeurs dans leurs
paramètres texte via la syntaxe ``{{nom}}``. Des variables intégrées
(``date``, ``heure``, ``iteration``) sont toujours disponibles.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

# Motif de substitution : {{ nom }} (espaces tolérés).
_TEMPLATE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


class VariableStore:
    """Conteneur de variables d'exécution avec substitution de gabarits."""

    def __init__(self, initial: dict[str, Any] | None = None, iteration: int = 0) -> None:
        self._vars: dict[str, Any] = dict(initial or {})
        self.iteration = iteration

    # -- Accès -------------------------------------------------------------
    def set(self, name: str, value: Any) -> None:
        """Définit (ou écrase) une variable."""
        self._vars[str(name)] = value

    def get(self, name: str, default: Any = None) -> Any:
        """Renvoie la valeur d'une variable (ou des variables intégrées)."""
        if name in self._vars:
            return self._vars[name]
        return self.builtins().get(name, default)

    def increment(self, name: str, by: float = 1) -> float:
        """Incrémente une variable numérique (créée à 0 si absente)."""
        try:
            current = float(self._vars.get(name, 0) or 0)
        except (TypeError, ValueError):
            current = 0.0
        value = current + float(by)
        # Conserve un entier si possible (confort d'affichage).
        if value.is_integer():
            value = int(value)
        self._vars[name] = value
        return value

    def builtins(self) -> dict[str, Any]:
        """Renvoie les variables intégrées, calculées à la volée."""
        now = datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "heure": now.strftime("%H:%M:%S"),
            "iteration": self.iteration,
        }

    def as_dict(self) -> dict[str, Any]:
        """Renvoie une copie des variables utilisateur + intégrées."""
        merged = dict(self.builtins())
        merged.update(self._vars)
        return merged

    # -- Substitution ------------------------------------------------------
    def resolve(self, value: Any) -> Any:
        """Substitue les ``{{var}}`` dans une chaîne ; renvoie tel quel sinon."""
        if not isinstance(value, str) or "{{" not in value:
            return value
        data = self.as_dict()

        def replace(match: re.Match) -> str:
            name = match.group(1)
            return str(data.get(name, match.group(0)))

        return _TEMPLATE.sub(replace, value)
