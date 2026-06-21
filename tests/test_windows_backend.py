"""Tests du backend de gestion des fenêtres (entièrement mocké)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from autoflow.core import windows_backend as wb


class FakeWindow:
    def __init__(self, title, hwnd=1234, fail=None):
        self.title = title
        self._hWnd = hwnd
        self._fail = fail
        self.activated = False

    def activate(self):
        self.activated = True
        if self._fail is not None:
            raise self._fail


def make_gw(windows):
    """Fabrique un faux module pygetwindow exposant getAllWindows()."""
    return SimpleNamespace(getAllWindows=lambda: windows)


def test_find_windows_contains(monkeypatch):
    wins = [FakeWindow("Bloc-notes — Sans titre"), FakeWindow("Chrome"), FakeWindow("")]
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw(wins))
    backend = wb.WindowsBackend()
    found = backend.find_windows("bloc-notes", "contains")
    assert len(found) == 1
    assert found[0].title.startswith("Bloc-notes")


def test_find_windows_exact(monkeypatch):
    wins = [FakeWindow("Cmder"), FakeWindow("Cmder - admin")]
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw(wins))
    backend = wb.WindowsBackend()
    assert len(backend.find_windows("Cmder", "exact")) == 1


def test_activate_appelle_activate(monkeypatch):
    win = FakeWindow("Cmder")
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([win]))
    backend = wb.WindowsBackend()
    assert backend.activate("Cmder") is True
    assert win.activated is True


def test_activate_introuvable(monkeypatch):
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([]))
    backend = wb.WindowsBackend()
    assert backend.activate("Inexistante") is False


def test_activate_neutralise_error_code_0(monkeypatch):
    erreur = Exception("Error code from Windows: 0 - L'opération a réussi")
    win = FakeWindow("Cmder", fail=erreur)
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([win]))
    backend = wb.WindowsBackend()
    # Ne doit PAS lever : l'« Error code 0 » est un faux échec.
    assert backend.activate("Cmder") is True


def test_activate_propage_vraie_erreur(monkeypatch):
    erreur = Exception("Error code from Windows: 5 - Accès refusé")
    win = FakeWindow("Cmder", fail=erreur)
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([win]))
    backend = wb.WindowsBackend()
    with pytest.raises(Exception):
        backend.activate("Cmder")


def test_activate_force_foreground(monkeypatch):
    win = FakeWindow("Cmder", hwnd=999)
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([win]))
    appels = []
    monkeypatch.setattr(wb, "force_foreground_window", lambda hwnd: appels.append(hwnd))
    backend = wb.WindowsBackend()
    backend.activate("Cmder", force_foreground=True)
    assert appels == [999]


def test_wait_for_window_apparait(monkeypatch):
    etats = {"compteur": 0}

    def fake_gw():
        etats["compteur"] += 1
        # Apparaît à la 3e vérification.
        wins = [FakeWindow("Cmder")] if etats["compteur"] >= 3 else []
        return make_gw(wins)

    monkeypatch.setattr(wb, "_get_gw", fake_gw)
    backend = wb.WindowsBackend()
    assert backend.wait_for_window("Cmder", timeout=10, sleep=lambda _s: None) is True


def test_wait_for_window_timeout(monkeypatch):
    monkeypatch.setattr(wb, "_get_gw", lambda: make_gw([]))
    backend = wb.WindowsBackend()
    assert backend.wait_for_window("Cmder", timeout=1, sleep=lambda _s: None) is False


def test_is_benign_error():
    assert wb._is_benign_error(Exception("Error code from Windows: 0 - ok"))
    assert not wb._is_benign_error(Exception("Error code from Windows: 5 - refusé"))


def test_matches():
    assert wb._matches("Bloc-notes", "bloc", "contains")
    assert not wb._matches("Bloc-notes", "Bloc", "exact")
    assert wb._matches("Cmder", "Cmder", "exact")


def test_force_foreground_window_hors_windows(monkeypatch):
    # Sur une plateforme non-Windows, l'appel doit être un no-op sans erreur.
    monkeypatch.setattr(wb.sys, "platform", "linux")
    wb.force_foreground_window(1234)  # ne doit pas lever


def test_launch_avec_arguments(monkeypatch):
    appels = {}

    class FakePopen:
        def __init__(self, cmd):
            appels["cmd"] = cmd

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    backend = wb.WindowsBackend()
    backend.launch("app.exe", ["--flag"])
    assert appels["cmd"] == ["app.exe", "--flag"]
