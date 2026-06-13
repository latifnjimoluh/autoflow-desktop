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


def test_settings_dialog_se_construit(app):
    from autoflow.gui.settings_dialog import SettingsDialog
    from autoflow.settings import Settings

    dialog = SettingsDialog(Settings(theme="light"))
    result = dialog.result_settings()
    assert result.theme == "light"


def test_history_dialog_se_construit(app):
    from autoflow.core.history import HistoryDB
    from autoflow.gui.history_dialog import HistoryDialog

    db = HistoryDB(":memory:")
    dialog = HistoryDialog(db)
    assert dialog.table.columnCount() == 7
    db.close()


def test_param_panel_montre_bouton_enfants_pour_condition(app):
    panel = ParamPanel()
    cond = registry.create_action("condition")
    panel.set_action(cond)
    # La présence d'un conteneur ajoute le bouton d'édition des sous-actions.
    assert cond.child_groups()


def test_sequence_editor_ajoute_et_edite(app):
    from autoflow.gui.sequence_editor import SequenceEditorWidget

    actions = []
    widget = SequenceEditorWidget(actions)
    widget._add("click")
    assert len(actions) == 1
    assert actions[0].type_name == "click"


def test_child_editor_pour_condition(app):
    from PySide6.QtWidgets import QTabWidget

    from autoflow.gui.child_editor import ChildEditorDialog

    cond = registry.create_action("condition")
    cond.then_actions = [registry.create_action("wait")]
    dialog = ChildEditorDialog(cond)
    tabs = dialog.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 2  # onglets « alors » et « sinon »


def test_export_python_action(app, tmp_path):
    window = MainWindow(autoload=False)
    window._add_action("type_text")
    wf = window._current()
    from autoflow.core.export_python import export_to_file
    import ast

    chemin = export_to_file(wf, tmp_path / "wf.py")
    ast.parse(chemin.read_text(encoding="utf-8"))
    window.close()
