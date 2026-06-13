"""Tests de l'historique d'exécution SQLite et des statistiques."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta

from autoflow.core.history import HistoryDB


def make_db():
    return HistoryDB(":memory:")


def test_record_et_liste():
    db = make_db()
    start = datetime(2026, 1, 1, 10, 0, 0)
    rid = db.record_run("WF1", start, start + timedelta(seconds=5), True, 3)
    assert rid == 1
    runs = db.list_runs()
    assert len(runs) == 1
    assert runs[0]["workflow"] == "WF1"
    assert runs[0]["duration"] == 5.0
    assert runs[0]["iterations"] == 3
    db.close()


def test_stats_taux_succes():
    db = make_db()
    base = datetime(2026, 1, 1, 10, 0, 0)
    db.record_run("WF", base, base + timedelta(seconds=2), True, 1)
    db.record_run("WF", base, base + timedelta(seconds=4), True, 1)
    db.record_run("WF", base, base + timedelta(seconds=6), False, 1, error="boom")
    stats = db.stats("WF")
    assert stats["total"] == 3
    assert stats["reussites"] == 2
    assert stats["echecs"] == 1
    assert abs(stats["taux_succes"] - 2 / 3) < 1e-9
    assert abs(stats["duree_moyenne"] - 4.0) < 1e-9
    db.close()


def test_filtrage_par_workflow():
    db = make_db()
    base = datetime(2026, 1, 1, 10, 0, 0)
    db.record_run("A", base, base + timedelta(seconds=1), True, 1)
    db.record_run("B", base, base + timedelta(seconds=1), True, 1)
    assert len(db.list_runs("A")) == 1
    assert db.stats("A")["total"] == 1
    db.close()


def test_export_csv(tmp_path):
    db = make_db()
    base = datetime(2026, 1, 1, 10, 0, 0)
    db.record_run("WF", base, base + timedelta(seconds=2), True, 1)
    chemin = db.export_csv(tmp_path / "histo.csv")
    assert chemin.exists()
    with chemin.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    assert lignes[0]["workflow"] == "WF"
    assert lignes[0]["success"] == "1"
    db.close()


def test_stats_base_vide():
    db = make_db()
    stats = db.stats()
    assert stats["total"] == 0
    assert stats["taux_succes"] == 0.0
    db.close()
