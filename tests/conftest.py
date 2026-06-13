"""Fixtures communes aux tests AutoFlow."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# Importe le paquet d'actions pour peupler le registre.
import autoflow.core.actions  # noqa: F401
from autoflow.persistence import store


@pytest.fixture(autouse=True)
def isolated_store(tmp_path_factory, monkeypatch):
    """Redirige le stockage des workflows vers un dossier temporaire.

    Évite que les tests (notamment GUI, qui sauvegardent à la fermeture) ne
    polluent le vrai dossier de données utilisateur.
    """
    base = tmp_path_factory.mktemp("autoflow_data")
    wf_dir = base / "workflows"
    wf_dir.mkdir()
    monkeypatch.setattr(store, "data_dir", lambda: base)
    monkeypatch.setattr(store, "workflows_dir", lambda: wf_dir)
    return base


@pytest.fixture
def inputs() -> MagicMock:
    """Façade d'entrées entièrement mockée (aucune action réelle)."""
    return MagicMock(name="InputBackend")


@pytest.fixture
def windows() -> MagicMock:
    """Façade de fenêtres mockée."""
    mock = MagicMock(name="WindowsBackend")
    mock.activate.return_value = True
    mock.wait_for_window.return_value = True
    return mock


@pytest.fixture
def context() -> dict:
    """Contexte d'exécution minimal avec un ``sleep`` neutre."""
    return {"sleep": lambda _s: None, "log": lambda *_a, **_k: None}
