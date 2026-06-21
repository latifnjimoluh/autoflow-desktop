"""Lot 2 — robustesse : secrets, globales, try/erreur, ET/OU, file d'attente."""

from __future__ import annotations

from unittest.mock import MagicMock

from autoflow.core import registry
from autoflow.core.actions.base import Action
from autoflow.core.executor import Executor
from autoflow.core.global_vars import GlobalVariables
from autoflow.models.workflow import Schedule, Workflow
from autoflow.services import run_queue
from autoflow.services.secrets import SecretVault


class _BoomAction(Action):
    """Action de test qui échoue toujours (non enregistrée au registre)."""

    type_name = "_boom"
    label = "Échoue toujours"

    def execute(self, inputs, windows, context):
        raise RuntimeError("boom")


def run(actions, **kwargs):
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=lambda _s: None, **kwargs)
    ex.run()
    return ex


# ---------------------------------------------------------- secrets
def test_vault_chiffre_et_dechiffre(tmp_path):
    vault = SecretVault(path=tmp_path / "v.vault", key_path=tmp_path / "v.key")
    vault.set("cle_api", "s3cr3t")
    assert vault.get("cle_api") == "s3cr3t"
    assert vault.names() == ["cle_api"]
    # Le fichier ne contient pas la valeur en clair.
    raw = (tmp_path / "v.vault").read_bytes()
    assert b"s3cr3t" not in raw


def test_vault_relecture_nouvelle_instance(tmp_path):
    SecretVault(path=tmp_path / "v.vault", key_path=tmp_path / "v.key").set("a", "b")
    again = SecretVault(path=tmp_path / "v.vault", key_path=tmp_path / "v.key")
    assert again.get("a") == "b"


def test_get_secret_action(tmp_path):
    vault = SecretVault(path=tmp_path / "v.vault", key_path=tmp_path / "v.key")
    vault.set("token", "xyz")
    action = registry.create_action("get_secret", params={
        "name": "token", "var_name": "t"})
    ex = run([action], secrets_vault=vault)
    assert ex.variables.get("t") == "xyz"


# ---------------------------------------------------------- globales
def test_global_set_get(tmp_path):
    glob = GlobalVariables(path=tmp_path / "g.json")
    actions = [
        registry.create_action("set_global", params={"name": "compteur", "value": "7"}),
    ]
    run(actions, globals_store=glob)
    assert glob.get("compteur") == "7"
    # Lecture dans une autre exécution.
    read = registry.create_action("get_global", params={
        "name": "compteur", "var_name": "v"})
    ex = run([read], globals_store=glob)
    assert ex.variables.get("v") == "7"


def test_global_persiste_sur_disque(tmp_path):
    GlobalVariables(path=tmp_path / "g.json").set("x", 1)
    assert GlobalVariables(path=tmp_path / "g.json").get("x") == 1


# ---------------------------------------------------------- try / erreur
def test_try_catch_execute_branche_erreur():
    catch = registry.create_action("set_variable", params={"name": "rattrape", "value": "oui"})
    try_block = registry.create_action("try_catch", params={"error_var": "err"})
    try_block.try_actions = [_BoomAction()]
    try_block.catch_actions = [catch]
    ex = run([try_block])
    assert ex.variables.get("rattrape") == "oui"
    assert "boom" in str(ex.variables.get("err"))


def test_try_catch_sans_erreur_ignore_branche():
    try_block = registry.create_action("try_catch")
    try_block.try_actions = [registry.create_action(
        "set_variable", params={"name": "ok", "value": "1"})]
    try_block.catch_actions = [registry.create_action(
        "set_variable", params={"name": "ko", "value": "1"})]
    ex = run([try_block])
    assert ex.variables.get("ok") == "1"
    assert ex.variables.get("ko") is None


# ---------------------------------------------------------- conditions ET/OU
def test_compound_condition_and_ou():
    windows = MagicMock()
    windows.find_windows.return_value = ["W"]  # fenêtre présente
    cond = registry.create_action("compound_condition", params={"logic": "AND"})
    cond.conditions = [
        {"test": "window_present", "title": "W", "match": "contains"},
        {"test": "variable_compare", "var_name": "n", "operator": ">", "value": "0"},
    ]
    cond.then_actions = [registry.create_action("set_variable", params={"name": "r", "value": "vrai"})]
    cond.else_actions = [registry.create_action("set_variable", params={"name": "r", "value": "faux"})]
    actions = [
        registry.create_action("set_variable", params={"name": "n", "value": "5"}),
        cond,
    ]
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, MagicMock(), windows, sleep_func=lambda _s: None)
    ex.run()
    assert ex.variables.get("r") == "vrai"  # ET : les deux vrais


def test_compound_condition_or_un_seul_vrai():
    from autoflow.core import conditions
    windows = MagicMock()
    windows.find_windows.return_value = []  # fenêtre absente
    context = {"variables": MagicMock()}
    context["variables"].resolve = lambda v: v
    context["variables"].get = lambda *_a: "5"
    tests = [
        {"test": "window_present", "title": "Z"},          # faux
        {"test": "variable_compare", "var_name": "n", "operator": ">", "value": "0"},  # vrai
    ]
    assert conditions.evaluate_all(tests, "OR", MagicMock(), windows, context) is True
    assert conditions.evaluate_all(tests, "AND", MagicMock(), windows, context) is False


# ---------------------------------------------------------- file d'attente
def test_run_queue_exclusif_refuse_pendant_execution():
    q = run_queue.RunQueue(mode="exclusive")
    order = []

    def long_runner():
        order.append("start")
        # Tente une seconde soumission pendant l'exécution.
        assert q.submit("b", lambda: order.append("b")) is False
        order.append("end")

    assert q.submit("a", long_runner) is True
    assert order == ["start", "end"]
    assert not q.is_busy()


def test_run_queue_file_enchaine():
    q = run_queue.RunQueue(mode="queue")
    order = []

    def first():
        order.append("a")
        q.submit("b", lambda: order.append("b"))  # mis en file

    q.submit("a", first)
    assert order == ["a", "b"]
    assert q.pending_count() == 0
