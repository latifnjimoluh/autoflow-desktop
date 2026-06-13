"""Tests des réglages persistants."""

from __future__ import annotations

from autoflow.settings import Settings


def test_defauts():
    s = Settings()
    assert s.failsafe is True
    assert s.theme == "dark"
    assert s.language == "fr"


def test_round_trip(tmp_path):
    s = Settings(theme="light", language="en", tesseract_path="C:/tess.exe",
                 notifications=False)
    chemin = s.save(tmp_path / "settings.json")
    rechargé = Settings.load(chemin)
    assert rechargé.theme == "light"
    assert rechargé.language == "en"
    assert rechargé.tesseract_path == "C:/tess.exe"
    assert rechargé.notifications is False


def test_load_absent_renvoie_defauts(tmp_path):
    s = Settings.load(tmp_path / "inexistant.json")
    assert s.theme == "dark"


def test_from_dict_ignore_champs_inconnus():
    s = Settings.from_dict({"theme": "light", "inconnu": 123})
    assert s.theme == "light"
    assert not hasattr(s, "inconnu")


def test_from_dict_champ_manquant_prend_defaut():
    s = Settings.from_dict({"theme": "light"})
    assert s.language == "fr"  # défaut conservé
