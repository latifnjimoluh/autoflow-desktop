"""Fixtures communes aux tests AutoFlow."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# Importe le paquet d'actions pour peupler le registre.
import autoflow.core.actions  # noqa: F401


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
