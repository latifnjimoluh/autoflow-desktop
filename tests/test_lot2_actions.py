"""Lot 2 — actions : fichiers, e-mail, son/voix, saisie, système, ciblage UI."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoflow.core import registry
from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow
from autoflow.services import email_smtp, system_control, tts


def run(actions, context_extra=None, **kwargs):
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=lambda _s: None, **kwargs)
    if context_extra:
        original = ex._make_context

        def patched():
            ctx = original()
            ctx.update(context_extra)
            return ctx
        ex._make_context = patched
    ex.run()
    return ex


# ---------------------------------------------------------- fichiers
def test_write_then_read_file(tmp_path):
    path = tmp_path / "note.txt"
    write = registry.create_action("write_file", params={
        "path": str(path), "content": "Bonjour", "append": False, "newline": False})
    read = registry.create_action("read_file", params={
        "path": str(path), "var_name": "c"})
    ex = run([write, read])
    assert ex.variables.get("c") == "Bonjour"


def test_file_operation_copie_et_supprime(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    dst = tmp_path / "sub" / "b.txt"
    copy = registry.create_action("file_operation", params={
        "operation": "copy", "source": str(src), "destination": str(dst)})
    run([copy])
    assert dst.exists()
    delete = registry.create_action("file_operation", params={
        "operation": "delete", "source": str(src)})
    run([delete])
    assert not src.exists()


def test_file_operation_create_folder(tmp_path):
    folder = tmp_path / "nouveau"
    action = registry.create_action("file_operation", params={
        "operation": "create_folder", "source": str(folder)})
    run([action])
    assert folder.is_dir()


# ---------------------------------------------------------- e-mail
def test_send_email_smtp_mocke():
    sent = {}

    def fake_sender(config, message):
        sent["to"] = message["To"]
        sent["subject"] = message["Subject"]
        sent["host"] = config.host

    settings = MagicMock(smtp_host="smtp.x", smtp_port=587, smtp_username="u",
                         smtp_use_tls=True, smtp_sender="me@x")
    action = registry.create_action("send_email", params={
        "to": "dest@x", "subject": "Sujet", "body": "Corps"})
    run([action], context_extra={"email_sender": fake_sender, "settings": settings})
    assert sent["to"] == "dest@x"
    assert sent["subject"] == "Sujet"


def test_email_build_message_avec_piece_jointe(tmp_path):
    pj = tmp_path / "r.txt"
    pj.write_text("data", encoding="utf-8")
    config = email_smtp.SmtpConfig(sender="me@x")
    msg = email_smtp.build_message(config, "to@x", "S", "B", attachment=str(pj))
    assert msg["To"] == "to@x"
    assert any(part.get_filename() == "r.txt" for part in msg.iter_attachments())


# ---------------------------------------------------------- son & voix
def test_speak_action_mocke():
    engine = MagicMock()
    action = registry.create_action("speak", params={"text": "salut"})
    ex = run([action], context_extra={"tts_engine": lambda: engine})
    engine.say.assert_called_once_with("salut")
    assert ex is not None


def test_tts_degradation_si_absent():
    # engine_factory qui lève → renvoie False sans crash.
    def boom():
        raise RuntimeError("pas de voix")
    assert tts.speak("x", engine_factory=boom) is False


def test_play_sound_beep_mocke():
    played = {}
    action = registry.create_action("play_sound", params={
        "mode": "beep", "frequency": 440, "duration_ms": 100})
    run([action], context_extra={"beep_player": lambda f, d: played.update(f=f, d=d)})
    assert played == {"f": 440, "d": 100}


# ---------------------------------------------------------- saisie utilisateur
def test_user_input_via_fournisseur():
    action = registry.create_action("user_input", params={
        "kind": "text", "prompt": "Nom ?", "var_name": "nom"})
    ex = run([action], context_extra={"input_provider": lambda req: "Alice"})
    assert ex.variables.get("nom") == "Alice"


def test_user_input_sans_fournisseur_defaut():
    action = registry.create_action("user_input", params={
        "kind": "text", "default": "rien", "var_name": "v"})
    ex = run([action])
    assert ex.variables.get("v") == "rien"


# ---------------------------------------------------------- système
def test_power_action_shutdown_exige_confirmation():
    calls = []

    def runner(cmd):
        calls.append(cmd)
        return 0
    # Sans confirmation → ignoré.
    action = registry.create_action("system_power", params={
        "action": "shutdown", "confirm": False})
    run([action], context_extra={"system_runner": runner})
    assert calls == []
    # Avec confirmation → commande exécutée (sur Windows uniquement).
    if system_control.is_windows():
        action2 = registry.create_action("system_power", params={
            "action": "shutdown", "confirm": True, "delay": 1})
        run([action2], context_extra={"system_runner": runner})
        assert calls and calls[0][0] == "shutdown"


def test_volume_action_mocke():
    levels = []
    action = registry.create_action("set_volume", params={"mute": False, "level": 42})
    run([action], context_extra={"volume_controller": levels.append})
    assert levels == [42]


def test_lock_session_degradation_hors_windows():
    # Sans runner sur OS non Windows → False, jamais d'exception.
    if not system_control.is_windows():
        assert system_control.lock_session() is False


# ---------------------------------------------------------- ciblage UI
def test_ui_element_click_via_backend():
    element = MagicMock()
    window = MagicMock()
    window.child_window.return_value = element
    backend = MagicMock()
    backend.window.return_value = window
    action = registry.create_action("ui_element", params={
        "operation": "click", "window": "Calc", "name": "Égale"})
    run([action], context_extra={"ui_backend": backend})
    element.click_input.assert_called_once()


def test_ui_element_indisponible_degrade():
    # Aucun backend + OS non Windows → action renvoie False sans crash.
    action = registry.create_action("ui_element", params={
        "operation": "click", "window": "X", "name": "Y"})
    ex = run([action])  # pas de ui_backend
    assert ex is not None
