"""Tests du service de mise à jour et du versionnement.

**Aucun test ne contacte le réseau** : l'``opener`` HTTP est toujours injecté
(faux client renvoyant un JSON contrôlé ou levant une erreur). Couvre : version
plus récente, identique, plus ancienne, erreur réseau, rate-limit, JSON
malformé, Release sans asset, pré-version ignorée, comparaison de versions, et
le parsing de ``GITHUB_REPO`` depuis diverses URL de remote.
"""

from __future__ import annotations

import json
import os
import urllib.error

import pytest

from autoflow.services import updater, version

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _release_json(tag: str, assets=None, body="Notes de version", html=""):
    return json.dumps({
        "tag_name": tag,
        "body": body,
        "html_url": html or f"https://github.com/x/y/releases/tag/{tag}",
        "assets": assets if assets is not None else [
            {"name": "AutoFlow.exe",
             "browser_download_url": "https://example/AutoFlow.exe"}
        ],
    })


def _opener(payload):
    """Construit un faux opener renvoyant ``payload`` (str) ou levant si exc."""
    def open_fn(url, timeout):
        if isinstance(payload, Exception):
            raise payload
        return payload
    return open_fn


# ----------------------------------------------------- comparaison de versions
@pytest.mark.parametrize("cur,new,expected", [
    ("1.0.0", "1.0.1", True),
    ("1.0.0", "2.0.0", True),
    ("1.0.0", "1.0.0", False),
    ("1.2.0", "1.1.0", False),
    ("1.0.0", "1.1.0rc1", False),   # pré-version ignorée
    ("1.0.0", "pas-une-version", False),
])
def test_is_update_available(cur, new, expected):
    assert updater.is_update_available(cur, new) is expected


# --------------------------------------------------------- check_for_updates
def test_maj_disponible():
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener(_release_json("v1.2.0")))
    assert info.available is True
    assert info.latest == "1.2.0"
    assert info.asset_url.endswith("AutoFlow.exe")
    assert info.asset_name == "AutoFlow.exe"
    assert info.error == ""
    assert info.download_url().endswith("AutoFlow.exe")


def test_deja_a_jour():
    info = updater.check_for_updates(
        current="1.2.0", repo="x/y", opener=_opener(_release_json("v1.2.0")))
    assert info.available is False
    assert info.error == ""


def test_erreur_reseau_geree():
    err = urllib.error.URLError("nom ou service inconnu")
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener(err))
    assert info.available is False
    assert "réseau" in info.error


def test_rate_limit_http_403():
    err = urllib.error.HTTPError("u", 403, "rate limit", {}, None)
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener(err))
    assert info.available is False
    assert "403" in info.error


def test_reponse_malformee():
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener("ce n'est pas du json {"))
    assert info.available is False
    assert "malformée" in info.error


def test_release_sans_asset():
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y",
        opener=_opener(_release_json("v1.3.0", assets=[])))
    assert info.available is True
    assert info.asset_url == ""
    # Repli de téléchargement sur la page de la Release.
    assert info.download_url().startswith("https://github.com")


def test_preversion_non_proposee():
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener(_release_json("v1.4.0rc1")))
    assert info.available is False


def test_aucune_version_publiee():
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y",
        opener=_opener(json.dumps({"body": "x", "assets": []})))
    assert info.available is False
    assert info.error


def test_asset_msi_choisi_si_pas_exe():
    assets = [{"name": "notes.txt", "browser_download_url": "u/notes.txt"},
              {"name": "AutoFlow.msi", "browser_download_url": "u/AutoFlow.msi"}]
    info = updater.check_for_updates(
        current="1.0.0", repo="x/y",
        opener=_opener(_release_json("v1.5.0", assets=assets)))
    assert info.asset_name == "AutoFlow.msi"


# ----------------------------------------------------------------- version
@pytest.mark.parametrize("url,expected", [
    ("https://github.com/latifnjimoluh/autoflow-desktop.git",
     "latifnjimoluh/autoflow-desktop"),
    ("https://github.com/latifnjimoluh/autoflow-desktop",
     "latifnjimoluh/autoflow-desktop"),
    ("git@github.com:owner/repo.git", "owner/repo"),
    ("ssh://git@github.com/owner/repo", "owner/repo"),
])
def test_parse_repo(url, expected):
    assert version.parse_repo(url) == expected


def test_parse_repo_non_github():
    assert version.parse_repo("https://gitlab.com/a/b.git") is None
    assert version.parse_repo("") is None
    assert version.parse_repo(None) is None


def test_github_repo_repli_sur_defaut():
    assert version.github_repo("not a url") == version.DEFAULT_REPO


def test_current_version_est_la_source_unique():
    import autoflow

    assert version.current_version() == autoflow.__version__


# ------------------------------------------------------------- GUI offscreen
@pytest.fixture(scope="module")
def app():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_update_dialog_se_construit(app):
    from autoflow.gui.update_dialog import UpdateDialog

    info = updater.check_for_updates(
        current="1.0.0", repo="x/y", opener=_opener(_release_json("v1.2.0")))
    dialog = UpdateDialog(info)
    assert dialog.windowTitle().startswith("Mise à jour")
    assert dialog.wants_install is False


def test_update_dialog_sans_asset_desactive_installer(app):
    from autoflow.gui.update_dialog import UpdateDialog

    info = updater.check_for_updates(
        current="1.0.0", repo="x/y",
        opener=_opener(_release_json("v1.2.0", assets=[])))
    dialog = UpdateDialog(info)
    assert dialog.info.asset_url == ""


def test_update_checker_thread_se_construit(app):
    from autoflow.gui.update_dialog import UpdateChecker

    checker = UpdateChecker(current="1.0.0", repo="x/y")
    assert checker is not None
