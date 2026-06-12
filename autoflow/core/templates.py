"""Galerie de modèles (templates) de workflows prêts à l'emploi.

Les modèles sont des fichiers JSON stockés dans ``examples/templates/``. Ils
réutilisent le **format de workflow existant**, enrichi de deux clés de
métadonnées facultatives — ``category`` et ``icon`` — ignorées par
``Workflow.from_dict`` (compatibilité ascendante intégrale).

Ce module charge les modèles, les regroupe par catégorie et permet de les
**cloner** dans l'espace de l'utilisateur (« Utiliser ce modèle »).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..models.workflow import Workflow


@dataclass
class Template:
    """Un modèle de la galerie : métadonnées + données de workflow."""

    id: str
    name: str
    description: str
    category: str = "Divers"
    icon: str = "📄"
    data: dict[str, Any] = field(default_factory=dict)

    def to_workflow(self) -> Workflow:
        """Construit un :class:`Workflow` éditable à partir du modèle."""
        return Workflow.from_dict(self.data)


def templates_dir() -> Path:
    """Renvoie le dossier des modèles fournis avec l'application."""
    return Path(__file__).resolve().parent.parent.parent / "examples" / "templates"


def load_templates(directory: str | Path | None = None) -> list[Template]:
    """Charge tous les modèles d'un dossier, triés par catégorie puis nom.

    Les fichiers illisibles sont ignorés (jamais d'exception propagée).
    """
    directory = Path(directory) if directory else templates_dir()
    templates: list[Template] = []
    if not directory.is_dir():
        return templates
    for file in sorted(directory.glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        templates.append(
            Template(
                id=file.stem,
                name=str(data.get("name", file.stem)),
                description=str(data.get("description", "")),
                category=str(data.get("category", "Divers")),
                icon=str(data.get("icon", "📄")),
                data=data,
            )
        )
    templates.sort(key=lambda t: (t.category.lower(), t.name.lower()))
    return templates


def templates_by_category(directory: str | Path | None = None) -> dict[str, list[Template]]:
    """Renvoie les modèles regroupés par catégorie (ordre préservé)."""
    grouped: dict[str, list[Template]] = {}
    for tpl in load_templates(directory):
        grouped.setdefault(tpl.category, []).append(tpl)
    return grouped


def categories(directory: str | Path | None = None) -> list[str]:
    """Renvoie la liste triée des catégories disponibles."""
    return sorted(templates_by_category(directory).keys(), key=str.lower)
