"""Lot 2 — données : boucle « pour chaque », CSV/Excel, HTTP, texte & maths."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from autoflow.core import data_sources, registry, safe_eval
from autoflow.core.executor import Executor
from autoflow.models.workflow import Schedule, Workflow
from autoflow.services import http_client


def run(actions, context_extra=None):
    """Exécute des actions et renvoie l'exécuteur (variables accessibles)."""
    wf = Workflow(name="T", schedule=Schedule(mode="run_once"), actions=actions)
    ex = Executor(wf, MagicMock(), MagicMock(), sleep_func=lambda _s: None)
    if context_extra:
        original = ex._make_context

        def patched():
            ctx = original()
            ctx.update(context_extra)
            return ctx
        ex._make_context = patched
    ex.run()
    return ex


# ---------------------------------------------------------- data_sources
def test_read_write_csv(tmp_path):
    path = tmp_path / "data.csv"
    rows = [{"nom": "Alice", "age": "30"}, {"nom": "Bob", "age": "25"}]
    data_sources.write_rows(path, rows)
    read = data_sources.read_rows(path)
    assert read == rows


def test_append_csv(tmp_path):
    path = tmp_path / "d.csv"
    data_sources.write_rows(path, [{"a": "1"}])
    data_sources.write_rows(path, [{"a": "2"}], append=True)
    assert [r["a"] for r in data_sources.read_rows(path)] == ["1", "2"]


def test_read_write_excel(tmp_path):
    pytest.importorskip("openpyxl")
    path = tmp_path / "data.xlsx"
    rows = [{"ville": "Paris", "pop": 2000000}, {"ville": "Lyon", "pop": 500000}]
    data_sources.write_rows(path, rows)
    read = data_sources.read_rows(path)
    assert read[0]["ville"] == "Paris"
    assert str(read[1]["pop"]) == "500000"


def test_iter_items_variable_csv_folder(tmp_path):
    assert data_sources.iter_items("variable", ["a", "b"]) == ["a", "b"]
    assert data_sources.iter_items("variable", "x, y, z") == ["x", "y", "z"]
    (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
    (tmp_path / "b.log").write_text("hi", encoding="utf-8")
    files = data_sources.iter_items("folder", str(tmp_path), pattern="*.txt")
    assert len(files) == 1 and files[0].endswith("a.txt")


# ---------------------------------------------------------- for_each
def test_for_each_sur_variable_accumule():
    actions = [
        registry.create_action("set_variable", params={"name": "liste", "value": "a,b,c"}),
        registry.create_action("for_each", params={
            "source": "variable", "variable": "liste",
            "item_var": "item", "index_var": "i"}),
    ]
    # Ajoute un corps qui incrémente un compteur et mémorise le dernier item.
    foreach = actions[1]
    foreach.body = [
        registry.create_action("increment_variable", params={"name": "n", "by": 1}),
        registry.create_action("set_variable", params={"name": "dernier", "value": "{{item}}"}),
    ]
    ex = run(actions)
    assert ex.variables.get("n") == 3
    assert ex.variables.get("dernier") == "c"


def test_for_each_garde_fou():
    foreach = registry.create_action("for_each", params={
        "source": "variable", "variable": "vals", "max_iterations": 2})
    foreach.body = [registry.create_action("increment_variable",
                                           params={"name": "n", "by": 1})]
    actions = [
        registry.create_action("set_variable", params={"name": "vals", "value": "1,2,3,4,5"}),
        foreach,
    ]
    ex = run(actions)
    assert ex.variables.get("n") == 2


def test_read_table_action(tmp_path):
    path = tmp_path / "c.csv"
    data_sources.write_rows(path, [{"x": "1"}, {"x": "2"}])
    action = registry.create_action("read_table", params={
        "path": str(path), "var_name": "lignes"})
    ex = run([action])
    assert ex.variables.get("lignes_count") == 2


# ---------------------------------------------------------- HTTP
def test_http_request_capture_reponse():
    def opener(method, url, headers, body, timeout):
        assert method == "GET"
        return 200, '{"id": 42, "name": "ok"}', {"Content-Type": "application/json"}

    action = registry.create_action("http_request", params={
        "method": "GET", "url": "https://api/x",
        "response_var": "rep", "json_path": "id"})
    ex = run([action], context_extra={"http_opener": opener})
    assert ex.variables.get("rep_status") == 200
    assert ex.variables.get("rep_value") == 42


def test_http_request_erreur_reseau_geree():
    def opener(*_a):
        raise OSError("pas de réseau")

    action = registry.create_action("http_request", params={
        "url": "https://api/x", "response_var": "rep"})
    ex = run([action], context_extra={"http_opener": opener})
    assert ex.variables.get("rep_status") == 0  # pas de crash


def test_http_client_post_envoie_corps():
    captured = {}

    def opener(method, url, headers, body, timeout):
        captured["method"] = method
        captured["body"] = body
        return 201, "{}", {}

    resp = http_client.request("POST", "https://x", headers={"A": "b"},
                               body='{"k":1}', opener=opener)
    assert resp.status == 201
    assert captured["method"] == "POST"
    assert captured["body"] == b'{"k":1}'


# ---------------------------------------------------------- texte & maths
@pytest.mark.parametrize("op,params,expected", [
    ("regex_extract", {"pattern": r"\d+"}, "42"),
    ("regex_replace", {"pattern": r"\d+", "replacement": "#"}, "il y a # chats"),
    ("upper", {}, "IL Y A 42 CHATS"),
    ("trim", {}, "il y a 42 chats"),
])
def test_text_transform(op, params, expected):
    base = {"operation": op, "text": "il y a 42 chats", "result_var": "r"}
    base.update(params)
    action = registry.create_action("text_transform", params=base)
    ex = run([action])
    assert ex.variables.get("r") == expected


def test_text_split_join():
    split = registry.create_action("text_transform", params={
        "operation": "split", "text": "a;b;c", "separator": ";", "result_var": "parts"})
    ex = run([split])
    assert ex.variables.get("parts") == ["a", "b", "c"]


def test_math_eval_action():
    actions = [
        registry.create_action("set_variable", params={"name": "prix", "value": "10"}),
        registry.create_action("set_variable", params={"name": "qte", "value": "3"}),
        registry.create_action("math_eval", params={
            "expression": "prix * qte * 2", "result_var": "total"}),
    ]
    ex = run(actions)
    assert ex.variables.get("total") == 60


@pytest.mark.parametrize("expr,expected", [
    ("2 + 3 * 4", 14),
    ("(1 + 2) ** 2", 9),
    ("max(3, 7, 2)", 7),
    ("round(sqrt(16))", 4),
])
def test_safe_eval_ok(expr, expected):
    assert safe_eval.evaluate(expr) == expected


@pytest.mark.parametrize("expr", ["__import__('os')", "open('x')", "a.b", "1 if True else 2"])
def test_safe_eval_rejette_code_dangereux(expr):
    with pytest.raises(ValueError):
        safe_eval.evaluate(expr)
