"""Actions de manipulation de texte (regex, découpe, casse…) et de calcul."""

from __future__ import annotations

import re
from typing import Any

from .. import safe_eval
from ..registry import register
from .base import Action, ParamSpec

TEXT_OPERATIONS = {
    "regex_extract": "Extraire (regex)",
    "regex_replace": "Remplacer (regex)",
    "split": "Découper",
    "join": "Joindre une liste",
    "upper": "Mettre en MAJUSCULES",
    "lower": "mettre en minuscules",
    "title": "Mettre Une Majuscule Par Mot",
    "trim": "Rogner les espaces",
    "replace": "Remplacer du texte",
}


@register
class TextTransformAction(Action):
    """Transforme une chaîne (ou une variable) et stocke le résultat."""

    type_name = "text_transform"
    label = "Manipuler du texte"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("operation", "Opération", "choice", "regex_extract",
                      choices=list(TEXT_OPERATIONS.keys())),
            ParamSpec("text", "Texte d'entrée", "text", "", supports_vars=True,
                      placeholder="Ex : {{reponse}}"),
            ParamSpec("pattern", "Motif (regex)", "str", "",
                      depends_on=("operation", ("regex_extract", "regex_replace")),
                      placeholder=r"Ex : \d+"),
            ParamSpec("replacement", "Remplacement", "str", "", supports_vars=True,
                      depends_on=("operation", ("regex_replace", "replace"))),
            ParamSpec("search", "Texte à chercher", "str", "",
                      depends_on=("operation", "replace")),
            ParamSpec("separator", "Séparateur", "str", ",",
                      depends_on=("operation", ("split", "join")),
                      placeholder="Ex : , ou ;"),
            ParamSpec("result_var", "Stocker le résultat dans", "variable", "resultat"),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        op = str(self.params.get("operation", "regex_extract"))
        store = (context or {}).get("variables")
        text = self._resolve(self.params.get("text", ""), context)
        result = self._apply(op, text, context)
        var = str(self.params.get("result_var", "")).strip()
        if store is not None and var:
            store.set(var, result)
        return result

    def _apply(self, op: str, text: Any, context: dict[str, Any]) -> Any:
        sep = str(self.params.get("separator", ","))
        if op == "regex_extract":
            match = re.search(str(self.params.get("pattern", "")), str(text))
            if not match:
                return ""
            return match.group(1) if match.groups() else match.group(0)
        if op == "regex_replace":
            repl = str(self._resolve(self.params.get("replacement", ""), context))
            return re.sub(str(self.params.get("pattern", "")), repl, str(text))
        if op == "replace":
            search = str(self.params.get("search", ""))
            repl = str(self._resolve(self.params.get("replacement", ""), context))
            return str(text).replace(search, repl)
        if op == "split":
            return [p for p in str(text).split(sep)]
        if op == "join":
            items = text if isinstance(text, list) else str(text).split(sep)
            return sep.join(str(i) for i in items)
        if op == "upper":
            return str(text).upper()
        if op == "lower":
            return str(text).lower()
        if op == "title":
            return str(text).title()
        if op == "trim":
            return str(text).strip()
        raise ValueError(f"Opération de texte inconnue : {op!r}")

    def summary(self) -> str:
        label = TEXT_OPERATIONS.get(str(self.params.get("operation", "")), "Texte")
        return f"{label} → {self.params.get('result_var')}"


@register
class MathAction(Action):
    """Évalue une expression arithmétique (variables autorisées) → variable."""

    type_name = "math_eval"
    label = "Calcul mathématique"
    category = "Variables"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("expression", "Expression", "str", "",
                      placeholder="Ex : (prix * quantite) * 1.2",
                      help="Variables et fonctions : abs, round, min, max, sqrt…"),
            ParamSpec("result_var", "Stocker le résultat dans", "variable", "total"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("expression", "")).strip():
            raise ValueError("L'expression ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        store = (context or {}).get("variables")
        env = store.as_dict() if store is not None else {}
        value = safe_eval.evaluate(str(self.params.get("expression", "")), env)
        var = str(self.params.get("result_var", "")).strip()
        if store is not None and var:
            store.set(var, value)
        return value

    def summary(self) -> str:
        return f"{self.params.get('result_var')} = {self.params.get('expression')}"
