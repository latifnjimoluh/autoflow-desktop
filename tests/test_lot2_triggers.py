"""Lot 2 — déclencheurs événementiels (détection simulée, aucun matériel réel)."""

from __future__ import annotations

from autoflow.core import triggers
from autoflow.core.triggers import create_trigger
from autoflow.core.triggers.idle_trigger import IdleTrigger
from autoflow.core.triggers.manager import TriggerManager


# ---------------------------------------------------------- fenêtre
def test_window_trigger_apparition():
    trig = create_trigger("window_event", params={
        "title": "Bloc", "event": "appears", "match": "contains"})
    assert trig.detect([], "") is None            # absente
    event = trig.detect(["Sans titre - Bloc-notes"], "Sans titre - Bloc-notes")
    assert event is not None
    assert "window_title" in event.variables
    # Ne se redéclenche pas tant qu'elle reste présente.
    assert trig.detect(["Sans titre - Bloc-notes"]) is None


def test_window_trigger_fermeture():
    trig = create_trigger("window_event", params={"title": "Jeu", "event": "closes"})
    trig.detect(["Jeu"])           # présente
    event = trig.detect([])        # disparue
    assert event is not None


def test_window_trigger_focus():
    trig = create_trigger("window_event", params={"title": "Chrome", "event": "focus"})
    assert trig.detect(["Chrome"], "Autre") is None
    assert trig.detect(["Chrome"], "Chrome") is not None


# ---------------------------------------------------------- fichier
def test_file_trigger_filtre_motif():
    trig = create_trigger("file_event", params={
        "folder": ".", "event": "created", "pattern": "*.pdf"})
    assert trig.handle_event("created", "/x/rapport.pdf") is not None
    assert trig.handle_event("created", "/x/photo.png") is None    # mauvais motif
    assert trig.handle_event("modified", "/x/rapport.pdf") is None  # mauvais événement


def test_file_trigger_any_event():
    trig = create_trigger("file_event", params={
        "folder": ".", "event": "any", "pattern": "*"})
    ev = trig.handle_event("deleted", "/x/f.txt")
    assert ev is not None and ev.variables["file_event"] == "deleted"


# ---------------------------------------------------------- presse-papiers
def test_clipboard_trigger_changement():
    trig = create_trigger("clipboard_event", params={"pattern": ""})
    assert trig.detect("premier") is None      # mémorise le 1er
    ev = trig.detect("deuxième")
    assert ev is not None and ev.variables["clipboard"] == "deuxième"
    assert trig.detect("deuxième") is None     # inchangé


def test_clipboard_trigger_regex():
    trig = create_trigger("clipboard_event", params={"pattern": r"https?://"})
    trig.detect("texte")                       # init
    assert trig.detect("encore du texte") is None    # ne correspond pas
    assert trig.detect("voir https://x.fr") is not None


# ---------------------------------------------------------- inactivité
def test_idle_trigger_seuil_et_rearmement():
    trig: IdleTrigger = create_trigger("idle_event", params={"minutes": 1})
    assert trig.detect(30) is None             # 30 s < 60 s
    ev = trig.detect(120)                       # franchit le seuil
    assert ev is not None
    assert trig.detect(150) is None            # déjà déclenché
    assert trig.detect(5) is None              # activité : réarme
    assert trig.detect(120) is not None        # re-déclenche


# ---------------------------------------------------------- webhook
def test_webhook_trigger_corps_json():
    trig = create_trigger("webhook_event", params={"port": 9999, "path": "/hook"})
    ev = trig.handle_request("/hook", '{"user": "alice", "n": 3}')
    assert ev is not None
    assert ev.variables["webhook_user"] == "alice"
    assert ev.variables["webhook_n"] == 3
    # Mauvais chemin ignoré.
    assert trig.handle_request("/autre", "{}") is None


# ---------------------------------------------------------- manager
def test_trigger_manager_route_les_evenements():
    fired = []
    manager = TriggerManager(run_workflow=lambda name, ev: fired.append((name, ev)))
    trig = create_trigger("window_event", params={"title": "X", "event": "appears"})
    manager.add("MonWorkflow", trig)
    # Simule un déclenchement direct.
    manager.start()  # window_event sans backend ne démarre pas, mais on émet à la main
    trig._on_fire = lambda ev: manager._dispatch("MonWorkflow", ev)
    trig.fire(triggers.TriggerEvent(trigger_type="window_event", message="x"))
    assert fired and fired[0][0] == "MonWorkflow"


def test_trigger_serialization_roundtrip():
    for type_name, _ in triggers.available_triggers():
        trig = create_trigger(type_name)
        data = trig.to_dict()
        clone = triggers.trigger_from_dict(data)
        assert clone.type_name == type_name
        assert clone.to_dict() == data
