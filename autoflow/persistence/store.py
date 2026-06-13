"""Sauvegarde, chargement, import et export des workflows au format JSON.

L'emplacement de stockage est déterminé via ``platformdirs`` (dossier de données
utilisateur), avec repli sur ``~/.autoflow`` si la dépendance est absente.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ..models.workflow import Workflow

_APP_NAME = "AutoFlow"


def data_dir() -> Path:
    """Renvoie (et crée) le dossier de données utilisateur d'AutoFlow."""
    try:
        from platformdirs import user_data_dir

        base = Path(user_data_dir(_APP_NAME, appauthor=False))
    except Exception:  # noqa: BLE001 - repli si platformdirs indisponible
        base = Path.home() / ".autoflow"
    base.mkdir(parents=True, exist_ok=True)
    return base


def workflows_dir() -> Path:
    """Renvoie (et crée) le sous-dossier contenant les workflows."""
    path = data_dir() / "workflows"
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(name: str) -> str:
    """Transforme un nom de workflow en nom de fichier sûr."""
    slug = re.sub(r"[^\w\-]+", "_", name.strip(), flags=re.UNICODE)
    slug = slug.strip("_")
    return slug or "workflow"


def save_workflow(workflow: Workflow, path: str | Path | None = None) -> Path:
    """Enregistre un workflow en JSON. Sans ``path``, utilise le dossier dédié."""
    if path is None:
        path = workflows_dir() / f"{slugify(workflow.name)}.json"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(workflow.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_workflow(path: str | Path) -> Workflow:
    """Charge un workflow depuis un fichier JSON."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Workflow.from_dict(data)


def list_workflows(directory: str | Path | None = None) -> list[tuple[Path, str]]:
    """Liste les workflows ``(chemin, nom)`` d'un dossier, triés par nom."""
    directory = Path(directory) if directory else workflows_dir()
    results: list[tuple[Path, str]] = []
    for file in sorted(directory.glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            name = str(data.get("name", file.stem))
        except (json.JSONDecodeError, OSError):
            name = file.stem
        results.append((file, name))
    return sorted(results, key=lambda item: item[1].lower())


def export_workflow(workflow: Workflow, path: str | Path) -> Path:
    """Exporte un workflow vers un emplacement choisi par l'utilisateur."""
    return save_workflow(workflow, path)


def import_workflow(path: str | Path) -> Workflow:
    """Importe un workflow depuis un fichier JSON externe."""
    return load_workflow(path)


def ensure_examples(directory: str | Path | None = None) -> int:
    """Copie les workflows d'exemple dans le dossier s'il est vide.

    Renvoie le nombre de fichiers copiés.
    """
    directory = Path(directory) if directory else workflows_dir()
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.glob("*.json")):
        return 0
    examples = Path(__file__).resolve().parent.parent.parent / "examples"
    if not examples.is_dir():
        return 0
    copied = 0
    for file in examples.glob("*.json"):
        shutil.copy2(file, directory / file.name)
        copied += 1
    return copied
