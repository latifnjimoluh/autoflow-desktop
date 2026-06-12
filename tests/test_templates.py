"""Tests de la galerie de modèles : chargement, métadonnées, clonage."""

from __future__ import annotations

import autoflow.core.actions  # noqa: F401 - peuple le registre
from autoflow.core import templates


def test_galerie_contient_assez_de_modeles():
    tpls = templates.load_templates()
    assert len(tpls) >= 15  # exigence : « au moins ~15 »


def test_chaque_modele_se_charge_en_workflow():
    for tpl in templates.load_templates():
        wf = tpl.to_workflow()
        assert wf.name == tpl.name
        # Les actions (y compris imbriquées) se reconstruisent sans erreur.
        for action in wf.actions:
            assert action.summary()


def test_modeles_categorises_et_avec_icones():
    for tpl in templates.load_templates():
        assert tpl.category
        assert tpl.icon
        assert tpl.description


def test_categories_multiples():
    cats = templates.categories()
    assert len(cats) >= 4
    assert "Productivité" in cats


def test_regroupement_par_categorie():
    grouped = templates.templates_by_category()
    total = sum(len(v) for v in grouped.values())
    assert total == len(templates.load_templates())


def test_clone_est_independant():
    """Cloner un modèle deux fois donne deux workflows distincts (pas d'alias)."""
    tpl = templates.load_templates()[0]
    wf1 = tpl.to_workflow()
    wf2 = tpl.to_workflow()
    wf1.name = "modifié"
    assert wf2.name != "modifié"
    if wf1.actions:
        wf1.actions[0].enabled = False
        assert wf2.actions[0].enabled is True
