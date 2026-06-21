"""Tests des services sous-jacents v3 (fenêtres, apps, touches, test d'action).

Toutes les dépendances liées à l'écran sont **mockées** : ces tests s'exécutent
sans affichage ni clavier réel.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import autoflow.core.actions  # noqa: F401 - peuple le registre
from autoflow.core import registry
from autoflow.services import apps, keys, windows_list

# Aliasé pour éviter que pytest ne collecte la fonction comme un test.
from autoflow.services.test_action import test_action as run_action


# -- Énumération des fenêtres ---------------------------------------------
def test_list_open_windows_filtre_et_trie():
    fake_windows = [
        SimpleNamespace(title="Zeta", _hWnd=3),
        SimpleNamespace(title="", _hWnd=0),       # ignorée (sans titre)
        SimpleNamespace(title="alpha", _hWnd=1),
        SimpleNamespace(title="alpha", _hWnd=9),  # doublon ignoré
    ]
    fake_gw = SimpleNamespace(getAllWindows=lambda: fake_windows)
    result = windows_list.list_open_windows(lambda: fake_gw)
    titres = [w.title for w in result]
    assert titres == ["alpha", "Zeta"]
    assert result[0].handle == 1


def test_list_open_windows_tolere_les_erreurs():
    def boom():
        raise RuntimeError("pas d'affichage")

    assert windows_list.list_open_windows(boom) == []


# -- Détection d'applications ---------------------------------------------
def test_list_installed_apps_scanne_les_raccourcis(tmp_path):
    (tmp_path / "Bloc-notes.lnk").write_text("")
    sub = tmp_path / "Outils"
    sub.mkdir()
    (sub / "Calculatrice.lnk").write_text("")
    found = apps.list_installed_apps([tmp_path], is_windows=True)
    noms = [a.name for a in found]
    assert "Bloc-notes" in noms
    assert "Calculatrice" in noms  # rglob explore les sous-dossiers


def test_list_installed_apps_dossier_absent_ok(tmp_path):
    assert apps.list_installed_apps([tmp_path / "introuvable"], is_windows=True) == []


# -- Capture / mapping des touches ----------------------------------------
def test_pynput_to_name_touche_caractere():
    assert keys.pynput_to_name(SimpleNamespace(char="A")) == "a"


def test_pynput_to_name_touche_speciale():
    assert keys.pynput_to_name(SimpleNamespace(char=None, name="ctrl_l")) == "ctrl"
    assert keys.pynput_to_name(SimpleNamespace(char=None, name="f5")) == "f5"
    assert keys.pynput_to_name(SimpleNamespace(char=None, name="page_up")) == "pageup"


def test_combo_to_keys_ordonne_les_modificateurs():
    assert keys.combo_to_keys(["shift", "ctrl"], "s") == ["ctrl", "shift", "s"]


def test_keys_to_label_lisible():
    assert keys.keys_to_label(["ctrl", "shift", "s"]) == "Ctrl + Maj + S"
    assert keys.keys_to_label("ctrl+end") == "Ctrl + Fin"  # libellé FR convivial


def test_normalize_key_alias_francais():
    assert keys.normalize_key("Entrée") == "enter"
    assert keys.normalize_key("Échap") == "esc"
    assert keys.normalize_key("Maj") == "shift"


def test_catalogue_touches_non_vide():
    assert len(keys.ALL_KEYS) > 50
    assert ("a", "A") in keys.ALL_KEYS


# -- Exécuteur « tester cette action » ------------------------------------
def test_test_action_succes():
    action = registry.create_action("type_text", params={"text": "salut"})
    inputs = MagicMock()
    result = run_action(action, inputs, MagicMock())
    assert result.ok is True
    inputs.type_text.assert_called_once()


def test_test_action_capture_erreur_de_validation():
    action = registry.create_action("key_press", params={"key": ""})
    result = run_action(action, MagicMock(), MagicMock())
    assert result.ok is False
    assert "touche" in result.error.lower()


def test_test_action_capture_exception_execution():
    action = registry.create_action("click", params={"x": 1, "y": 1})
    inputs = MagicMock()
    inputs.click.side_effect = RuntimeError("échec souris")
    result = run_action(action, inputs, MagicMock())
    assert result.ok is False
    assert "échec souris" in result.error
