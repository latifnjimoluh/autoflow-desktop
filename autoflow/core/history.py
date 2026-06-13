"""Historique d'exécution et statistiques, stockés en SQLite local.

Utilise le module standard :mod:`sqlite3` — **aucun serveur, aucun Docker,
aucune installation**. La base est un simple fichier (ou ``:memory:`` en test).
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration REAL,
    success INTEGER NOT NULL DEFAULT 0,
    iterations INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
"""


class HistoryDB:
    """Journalise chaque exécution de workflow et calcule des statistiques."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- Écriture ----------------------------------------------------------
    def record_run(self, workflow: str, started_at: datetime, ended_at: datetime,
                   success: bool, iterations: int, error: str | None = None) -> int:
        """Enregistre une exécution terminée et renvoie son identifiant."""
        duration = (ended_at - started_at).total_seconds()
        cur = self._conn.execute(
            "INSERT INTO runs (workflow, started_at, ended_at, duration, success, "
            "iterations, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (workflow, started_at.isoformat(timespec="seconds"),
             ended_at.isoformat(timespec="seconds"), duration,
             1 if success else 0, int(iterations), error),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    # -- Lecture -----------------------------------------------------------
    def list_runs(self, workflow: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Renvoie les exécutions (les plus récentes d'abord)."""
        query = "SELECT * FROM runs"
        params: list[Any] = []
        if workflow:
            query += " WHERE workflow = ?"
            params.append(workflow)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return [dict(row) for row in self._conn.execute(query, params)]

    def stats(self, workflow: str | None = None) -> dict[str, Any]:
        """Calcule des statistiques simples (total, taux de succès, durées)."""
        where = " WHERE workflow = ?" if workflow else ""
        params = [workflow] if workflow else []
        row = self._conn.execute(
            f"SELECT COUNT(*) AS total, "
            f"COALESCE(SUM(success), 0) AS reussites, "
            f"COALESCE(AVG(duration), 0) AS duree_moy, "
            f"MAX(ended_at) AS derniere FROM runs{where}",
            params,
        ).fetchone()
        total = row["total"] or 0
        reussites = row["reussites"] or 0
        return {
            "total": total,
            "reussites": reussites,
            "echecs": total - reussites,
            "taux_succes": (reussites / total) if total else 0.0,
            "duree_moyenne": row["duree_moy"] or 0.0,
            "derniere_execution": row["derniere"],
        }

    # -- Export ------------------------------------------------------------
    def export_csv(self, path: str | Path) -> Path:
        """Exporte tout l'historique au format CSV."""
        path = Path(path)
        rows = self.list_runs(limit=1_000_000)
        champs = ["id", "workflow", "started_at", "ended_at", "duration",
                  "success", "iterations", "error"]
        with path.open("w", newline="", encoding="utf-8") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=champs)
            writer.writeheader()
            for row in reversed(rows):  # ordre chronologique
                writer.writerow({k: row.get(k) for k in champs})
        return path

    def close(self) -> None:
        """Ferme la connexion SQLite."""
        self._conn.close()


def default_history_path() -> Path:
    """Renvoie le chemin du fichier d'historique dans le dossier de données."""
    from ..persistence import store

    return store.data_dir() / "history.db"
