"""Smoke tests de l'interface (mode hors écran « offscreen »).

Ces tests vérifient que la fenêtre principale et ses panneaux se construisent
sans erreur, sans toucher au matériel ni nécessiter d'affichage réel.
"""

from __future__ import annotations

import os

import pytest

# Force le rendu hors écran avant toute importation de Qt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from autoflow.core import registry  # noqa: E402
from autoflow.gui.action_editor import ActionEditorPanel  # noqa: E402
from autoflow.gui.main_window import MainWindow  # noqa: E402
from autoflow.gui.param_panel import ParamPanel  # noqa: E402


@pytest.fixture(scope="module")
def app():
    """Instance unique de QApplication pour les tests GUI."""
    application = QApplication.instance() or QApplication([])
    yield application


def test_fenetre_principale_se_construit(app):
    """La fenêtre principale se construit sans erreur (sans autoload disque)."""
    window = MainWindow(autoload=False)
    assert window.windowTitle().startswith("AutoFlow")
    assert window._current() is not None
    window.close()


def test_ajout_et_suppression_action(app):
    window = MainWindow(autoload=False)
    wf = window._current()
    before = len(wf.actions)
    window._add_action("click")
    assert len(wf.actions) == before + 1
    window.action_panel.list.setCurrentRow(len(wf.actions) - 1)
    window._remove_action()
    assert len(wf.actions) == before
    window.close()


def test_param_panel_genere_formulaire(app):
    panel = ParamPanel()
    action = registry.create_action("type_text", params={"text": "salut"})
    panel.set_action(action)
    # Le formulaire doit contenir des lignes (activée, délai, paramètres).
    assert panel._layout.rowCount() > 1


def test_action_editor_menu_par_categorie(app):
    panel = ActionEditorPanel()
    menu = panel._add_button.menu()
    assert menu is not None
    # Le menu regroupe les actions par catégorie (au moins un sous-menu).
    assert len(menu.actions()) >= 1


def test_toggle_action_change_etat(app):
    window = MainWindow(autoload=False)
    window._add_action("wait")
    wf = window._current()
    row = len(wf.actions) - 1
    window.action_panel.list.setCurrentRow(row)
    etat = wf.actions[row].enabled
    window._toggle_action()
    assert wf.actions[row].enabled is not etat
    window.close()
