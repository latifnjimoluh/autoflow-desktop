"""Tests du démarrage automatique Windows (winreg mocké, sans toucher au registre)."""

from __future__ import annotations

import sys
import types

import pytest

from autoflow import autostart


class FakeWinreg(types.SimpleNamespace):
    """Faux module winreg en mémoire (n'écrit jamais dans le vrai registre)."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_SET_VALUE = 1
    KEY_QUERY_VALUE = 2
    REG_SZ = 3

    def __init__(self):
        super().__init__()
        self.store: dict[str, str] = {}

    def OpenKey(self, root, path, reserved, access):  # noqa: N802
        store = self.store
        backend = self

        class _Key:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

        key = _Key()
        key._store = store
        key._backend = backend
        return key

    def SetValueEx(self, key, name, reserved, type_, value):  # noqa: N802
        self.store[name] = value

    def DeleteValue(self, key, name):  # noqa: N802
        if name not in self.store:
            raise FileNotFoundError(name)
        del self.store[name]

    def QueryValueEx(self, key, name):  # noqa: N802
        if name not in self.store:
            raise FileNotFoundError(name)
        return self.store[name], self.REG_SZ


@pytest.fixture
def fake_registry(monkeypatch):
    fake = FakeWinreg()
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(autostart, "is_windows", lambda: True)
    return fake


def test_enable_disable_round_trip(fake_registry):
    assert autostart.is_enabled() is False
    assert autostart.enable() is True
    assert autostart.is_enabled() is True
    assert autostart.disable() is True
    assert autostart.is_enabled() is False


def test_disable_absent_renvoie_true(fake_registry):
    assert autostart.disable() is True


def test_noop_hors_windows(monkeypatch):
    monkeypatch.setattr(autostart, "is_windows", lambda: False)
    assert autostart.enable() is False
    assert autostart.disable() is False
    assert autostart.is_enabled() is False
