"""Tests de la persistance des workflows."""

from __future__ import annotations

import json

import pytest

from autoflow.core import registry
from autoflow.models.workflow import Schedule, Workflow
from autoflow.persistence import store


def sample_workflow() -> Workflow:
    return Workflow(
        name="Démo é à ç",
        description="Un workflow de test",
        schedule=Schedule(mode="loop_interval", interval_seconds=900, max_iterations=0),
        actions=[
            registry.create_action("activate_window",
                                    params={"title": "Bloc-notes"}, delay_after=0.3),
            registry.create_action("hotkey", params={"keys": ["ctrl", "end"]}),
            registry.create_action("type_text", params={"text": "."}),
        ],
    )


def test_save_load_round_trip(tmp_path):
    wf = sample_workflow()
    path = store.save_workflow(wf, tmp_path / "demo.json")
    assert path.exists()
    rechargé = store.load_workflow(path)
    assert rechargé == wf
    assert rechargé.to_dict() == wf.to_dict()


def test_json_lisible_utf8(tmp_path):
    wf = sample_workflow()
    path = store.save_workflow(wf, tmp_path / "demo.json")
    contenu = path.read_text(encoding="utf-8")
    assert "Bloc-notes" in contenu
    # Les accents ne doivent pas être échappés (ensure_ascii=False).
    assert "é à ç" in contenu


def test_export_puis_import(tmp_path):
    wf = sample_workflow()
    chemin = tmp_path / "export.json"
    store.export_workflow(wf, chemin)
    importé = store.import_workflow(chemin)
    assert importé == wf


def test_list_workflows(tmp_path):
    store.save_workflow(Workflow(name="Bravo"), tmp_path / "b.json")
    store.save_workflow(Workflow(name="Alpha"), tmp_path / "a.json")
    listing = store.list_workflows(tmp_path)
    noms = [nom for _path, nom in listing]
    assert noms == ["Alpha", "Bravo"]


def test_slugify():
    assert store.slugify("Anti-veille Bloc-notes") == "Anti-veille_Bloc-notes"
    assert store.slugify("   ") == "workflow"


def test_ensure_examples_copie_si_vide(tmp_path):
    copied = store.ensure_examples(tmp_path)
    assert copied >= 2
    fichiers = list(tmp_path.glob("*.json"))
    assert len(fichiers) == copied
    # Une seconde fois : rien n'est copié car le dossier n'est plus vide.
    assert store.ensure_examples(tmp_path) == 0


def test_load_workflow_corrompu(tmp_path):
    mauvais = tmp_path / "bad.json"
    mauvais.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        store.load_workflow(mauvais)


def test_data_dir_existe():
    chemin = store.data_dir()
    assert chemin.exists()
