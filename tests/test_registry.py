"""Tests du registre / fabrique d'actions."""

from __future__ import annotations

import pytest

from autoflow.core import registry
from autoflow.core.actions.base import Action, ParamSpec


def test_available_types_non_vide():
    types = dict(registry.available_types())
    # Quelques types core doivent être présents.
    for expected in ("click", "type_text", "hotkey", "activate_window", "wait"):
        assert expected in types


def test_create_action_par_type():
    action = registry.create_action("type_text", params={"text": "salut"})
    assert action.type_name == "type_text"
    assert action.params["text"] == "salut"


def test_type_inconnu_leve_erreur_claire():
    with pytest.raises(registry.UnknownActionError):
        registry.create_action("type_inexistant")


def test_action_from_dict_sans_type():
    with pytest.raises(ValueError):
        registry.action_from_dict({"params": {}})


def test_register_refuse_type_vide():
    class SansType(Action):
        type_name = ""

        def execute(self, inputs, windows, context):
            return None

    with pytest.raises(ValueError):
        registry.register(SansType)


def test_register_et_creation_dynamique():
    class Custom(Action):
        type_name = "custom_test_action"
        label = "Action de test"

        @classmethod
        def param_specs(cls):
            return [ParamSpec("valeur", "Valeur", "int", 42)]

        def execute(self, inputs, windows, context):
            return self.params["valeur"]

    try:
        registry.register(Custom)
        action = registry.create_action("custom_test_action")
        assert action.params["valeur"] == 42
        assert action.execute(None, None, {}) == 42
    finally:
        registry.all_classes().pop("custom_test_action", None)
        registry._REGISTRY.pop("custom_test_action", None)
