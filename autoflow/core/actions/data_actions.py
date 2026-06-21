"""Actions pilotées par les données : boucle « pour chaque », lecture/écriture
de tableaux (CSV/Excel). Étendent le moteur sans casser le format existant.
"""

from __future__ import annotations

from typing import Any

from .. import data_sources
from ..registry import action_from_dict, register
from .base import Action, ParamSpec

# Sources proposées pour la boucle « pour chaque » (valeur -> libellé FR).
FOREACH_SOURCES = {
    "variable": "Éléments d'une variable / liste",
    "table": "Lignes d'un fichier CSV ou Excel",
    "folder": "Fichiers d'un dossier",
    "lines": "Lignes d'un fichier texte",
}


@register
class ForEachAction(Action):
    """Répète un corps d'actions **pour chaque élément** d'une source de données.

    Expose dans le corps les variables ``item`` (élément courant) et ``index``
    (position, à partir de 0). Un garde-fou limite le nombre d'itérations.
    """

    type_name = "for_each"
    label = "Pour chaque élément (boucle de données)"
    category = "Contrôle"

    def __init__(self, *args: Any, body=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.body: list[Action] = list(body or [])

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("source", "Source des éléments", "choice", "variable",
                      choices=list(FOREACH_SOURCES.keys()),
                      help="D'où proviennent les éléments à parcourir."),
            ParamSpec("variable", "Variable / liste", "variable", "",
                      supports_vars=True, depends_on=("source", "variable"),
                      help="Variable contenant une liste (ou texte séparé par virgules)."),
            ParamSpec("path", "Fichier", "file", "",
                      depends_on=("source", ("table", "lines")),
                      placeholder="Ex : C:\\data\\clients.csv"),
            ParamSpec("folder", "Dossier", "folder", "",
                      depends_on=("source", "folder")),
            ParamSpec("pattern", "Filtre (motif)", "str", "*",
                      depends_on=("source", "folder"),
                      placeholder="Ex : *.png"),
            ParamSpec("has_header", "Le tableau a une ligne d'en-tête", "bool", True,
                      depends_on=("source", "table")),
            ParamSpec("item_var", "Nom de la variable « élément »", "variable", "item"),
            ParamSpec("index_var", "Nom de la variable « index »", "variable", "index"),
            ParamSpec("max_iterations", "Garde-fou : itérations max", "int", 10000,
                      min_value=1),
        ]

    def child_groups(self) -> dict[str, list[Action]]:
        return {"corps": self.body}

    def _items(self, context: dict[str, Any]) -> list[Any]:
        source = str(self.params.get("source", "variable"))
        if source == "variable":
            store = (context or {}).get("variables")
            name = str(self.params.get("variable", "")).strip()
            raw = store.get(name) if store is not None else None
            if raw is None:
                raw = self._resolve(self.params.get("variable", ""), context)
            return data_sources.iter_items("variable", raw)
        if source in ("table", "lines"):
            path = str(self._resolve(self.params.get("path", ""), context))
            return data_sources.iter_items(
                source, path, has_header=bool(self.params.get("has_header", True)))
        if source == "folder":
            folder = str(self._resolve(self.params.get("folder", ""), context))
            return data_sources.iter_items(
                "folder", folder, pattern=str(self.params.get("pattern", "*") or "*"))
        return []

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        items = self._items(context)
        guard = int(self.params.get("max_iterations", 10000) or 10000)
        store = (context or {}).get("variables")
        runner = (context or {}).get("run_actions")
        item_var = str(self.params.get("item_var", "item")).strip() or "item"
        index_var = str(self.params.get("index_var", "index")).strip() or "index"
        done = 0
        for index, item in enumerate(items):
            if done >= guard:
                log = (context or {}).get("log")
                if callable(log):
                    log(f"Boucle « pour chaque » stoppée au garde-fou ({guard}).",
                        "warning")
                break
            if store is not None:
                store.set(item_var, item)
                store.set(index_var, index)
            if callable(runner):
                runner(self.body)
            done += 1
        return done

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["body"] = [a.to_dict() for a in self.body]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForEachAction:
        return cls(
            params=data.get("params"),
            enabled=data.get("enabled", True),
            delay_after=data.get("delay_after", 0.0),
            retries=data.get("retries", 0),
            retry_delay=data.get("retry_delay", 0.0),
            on_error=data.get("on_error", "inherit"),
            delay_jitter=data.get("delay_jitter", 0.0),
            body=[action_from_dict(d) for d in data.get("body", [])],
        )

    def summary(self) -> str:
        label = FOREACH_SOURCES.get(str(self.params.get("source", "")), "éléments")
        return f"Pour chaque : {label} ({len(self.body)} action(s))"


@register
class ReadTableAction(Action):
    """Lit un fichier CSV/Excel dans une variable (liste de lignes)."""

    type_name = "read_table"
    label = "Lire un tableau (CSV/Excel)"
    category = "Données"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Fichier à lire", "file", "",
                      placeholder="Ex : C:\\data\\clients.xlsx"),
            ParamSpec("has_header", "Première ligne = en-tête", "bool", True),
            ParamSpec("var_name", "Stocker les lignes dans la variable",
                      "variable", "lignes"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin du fichier ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        path = str(self._resolve(self.params.get("path", ""), context))
        rows = data_sources.read_rows(
            path, has_header=bool(self.params.get("has_header", True)))
        store = (context or {}).get("variables")
        var = str(self.params.get("var_name", "")).strip()
        if store is not None and var:
            store.set(var, rows)
            store.set(f"{var}_count", len(rows))
        log = (context or {}).get("log")
        if callable(log):
            log(f"{len(rows)} ligne(s) lue(s) depuis {path}.", "info")
        return rows

    def summary(self) -> str:
        return f"Lire « {self.params.get('path')} » → {self.params.get('var_name')}"


@register
class WriteTableAction(Action):
    """Écrit/ajoute des lignes dans un CSV/Excel depuis une variable liste."""

    type_name = "write_table"
    label = "Écrire un tableau (CSV/Excel)"
    category = "Données"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("path", "Fichier de destination", "file", "",
                      placeholder="Ex : C:\\rapports\\sortie.csv"),
            ParamSpec("var_name", "Variable contenant les lignes", "variable",
                      "lignes", help="Liste de dictionnaires (ex. issue de « Lire un tableau »)."),
            ParamSpec("append", "Ajouter à la suite (sinon écraser)", "bool", False),
        ]

    def validate(self) -> None:
        if not str(self.params.get("path", "")).strip():
            raise ValueError("Le chemin du fichier ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        path = str(self._resolve(self.params.get("path", ""), context))
        store = (context or {}).get("variables")
        var = str(self.params.get("var_name", "")).strip()
        rows = store.get(var) if (store is not None and var) else []
        rows = self._normalise(rows)
        data_sources.write_rows(path, rows, append=bool(self.params.get("append", False)))
        log = (context or {}).get("log")
        if callable(log):
            log(f"{len(rows)} ligne(s) écrite(s) dans {path}.", "info")
        return len(rows)

    @staticmethod
    def _normalise(rows: Any) -> list[dict[str, Any]]:
        """Tolère une liste de dicts, de listes, ou de scalaires."""
        if not isinstance(rows, list):
            return []
        out: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, dict):
                out.append(row)
            elif isinstance(row, (list, tuple)):
                out.append({f"col{i + 1}": v for i, v in enumerate(row)})
            else:
                out.append({"valeur": row})
        return out

    def summary(self) -> str:
        mode = "ajout" if self.params.get("append") else "écrasement"
        return f"Écrire {self.params.get('var_name')} → {self.params.get('path')} ({mode})"
