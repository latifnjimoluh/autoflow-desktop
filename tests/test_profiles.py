"""Tests des profils / espaces de travail."""

from __future__ import annotations

from autoflow.models.workflow import Workflow
from autoflow.persistence import profiles, store


def test_profil_par_defaut_cree():
    noms = profiles.list_profiles()
    assert profiles.DEFAULT_PROFILE in noms


def test_creation_et_bascule():
    profiles.create_profile("Travail")
    profiles.create_profile("Jeux")
    noms = profiles.list_profiles()
    assert "Travail" in noms and "Jeux" in noms


def test_workflows_isoles_par_profil():
    d_travail = profiles.profile_workflows_dir("Travail")
    store.save_workflow(Workflow(name="Boulot"), d_travail / "boulot.json")
    d_jeux = profiles.profile_workflows_dir("Jeux")
    # Le profil « Jeux » ne voit pas le workflow de « Travail ».
    assert store.list_workflows(d_jeux) == []
    assert len(store.list_workflows(d_travail)) == 1


def test_suppression_profil():
    profiles.create_profile("Garde")  # garantit qu'il restera un profil
    profiles.create_profile("Temporaire")
    assert profiles.delete_profile("Temporaire") is True
    assert "Temporaire" not in profiles.list_profiles()


def test_refus_suppression_dernier_profil(monkeypatch):
    # Simule un unique profil restant.
    monkeypatch.setattr(profiles, "list_profiles", lambda: ["Seul"])
    assert profiles.delete_profile("Seul") is False
