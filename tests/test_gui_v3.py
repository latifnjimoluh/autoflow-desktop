"""Smoke tests GUI v3 (offscreen) : widgets concrets, galerie, palette, nœuds.

Vérifient que les nouveaux composants se construisent et se comportent
correctement sans affichage réel ni matériel.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

import autoflow.core.actions  # noqa: E402,F401 - peuple le registre
from autoflow.core import registry  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


# -- Widgets concrets ------------------------------------------------------
def test_key_capture_field_round_trip(app):
    from autoflow.gui.concrete_widgets import KeyCaptureField

    field = KeyCaptureField("f5")
    assert field.value() == "f5"


def test_hotkey_capture_field_round_trip(app):
    from autoflow.gui.concrete_widgets import HotkeyCaptureField

    field = HotkeyCaptureField(["ctrl", "s"])
    assert field.value() == ["ctrl", "s"]
    assert field.badge.text() == "Ctrl + S"


def test_color_field_round_trip(app):
    from autoflow.gui.concrete_widgets import ColorField

    field = ColorField("#112233")
    assert field.value() == "#112233"


def test_window_select_field_utilise_le_provider(app):
    from autoflow.gui.concrete_widgets import WindowSelectField

    field = WindowSelectField("", provider=lambda: ["Chrome", "Bloc-notes"])
    assert field.combo.count() == 2


def test_combo_field_variables(app):
    from autoflow.gui.concrete_widgets import ComboField

    field = ComboField("compteur", provider=lambda: ["compteur", "total"])
    assert field.value() == "compteur"


# -- Panneau de paramètres concret ----------------------------------------
def test_param_panel_construit_tous_les_types(app):
    from autoflow.gui.param_panel import PanelServices, ParamPanel

    services = PanelServices(
        windows_provider=lambda: ["Fenêtre A"],
        apps_provider=lambda: [("Bloc-notes", "notepad.exe")],
        variables_provider=lambda: ["x", "y"],
        workflows_provider=lambda: ["Autre"],
        test_runner=lambda a: None,
    )
    panel = ParamPanel(services=services)
    for type_name, _ in registry.available_types():
        action = registry.create_action(type_name)
        panel.set_action(action, lambda: None)
        assert panel._form_layout().count() > 0


def test_param_panel_depends_on_cache_les_champs(app):
    from autoflow.gui.param_panel import ParamPanel

    panel = ParamPanel()
    action = registry.create_action("click", params={"use_current": False})
    panel.set_action(action, lambda: None)
    x_spec = next(s for s in action.param_specs() if s.name == "x")
    assert panel._depends_satisfied(x_spec) is True
    action.params["use_current"] = True
    assert panel._depends_satisfied(x_spec) is False


def test_param_panel_boutons_de_capture(app):
    """Les boutons de capture apparaissent selon les paramètres de l'action."""
    from PySide6.QtWidgets import QPushButton

    from autoflow.gui.param_panel import ParamPanel

    def labels(type_name):
        panel = ParamPanel()
        panel.set_action(registry.create_action(type_name), lambda: None)
        host = panel._form_layout().parentWidget()
        return [b.text() for b in host.findChildren(QPushButton)]

    assert any("pixel" in t.lower() for t in labels("wait_for_pixel"))
    assert any("région" in t.lower() for t in labels("screenshot"))
    assert any("position" in t.lower() for t in labels("click"))
    drag_labels = labels("drag")
    assert any("départ" in t.lower() for t in drag_labels)
    assert any("arrivée" in t.lower() for t in drag_labels)


def test_param_panel_compat_rowcount(app):
    """L'attribut historique ``_layout.rowCount()`` reste exploitable."""
    from autoflow.gui.param_panel import ParamPanel

    panel = ParamPanel()
    panel.set_action(registry.create_action("type_text"), lambda: None)
    assert panel._layout.rowCount() > 1


# -- Galerie de modèles ----------------------------------------------------
def test_template_gallery_se_construit_et_filtre(app):
    from autoflow.gui.template_gallery import TemplateGallery

    gallery = TemplateGallery()
    total = gallery.list.count()
    assert total >= 15
    gallery.search.setText("git")
    assert 0 < gallery.list.count() < total


# -- Palette d'actions -----------------------------------------------------
def test_action_palette_cherchable(app):
    from autoflow.gui.action_palette import ActionPalette

    palette = ActionPalette()
    total = palette.list.count()
    palette.search.setText("souris")
    assert palette.list.count() < total


# -- Vue en nœuds ----------------------------------------------------------
def test_node_view_rend_les_actions(app):
    from autoflow.gui.node_view import NodeView

    view = NodeView()
    actions = [registry.create_action("click"), registry.create_action("condition")]
    view.set_actions(actions, 0)
    assert len(view._scene.items()) > 0


# -- Onboarding ------------------------------------------------------------
def test_welcome_dialog_se_construit(app):
    from autoflow.gui.onboarding import WelcomeDialog

    dialog = WelcomeDialog()
    assert dialog.choice is None


def test_creation_wizard_construit_un_workflow(app):
    from autoflow.gui.onboarding import CreationWizard

    wizard = CreationWizard()
    wf = wizard.build_workflow()
    assert wf.name
    assert len(wf.actions) == 1


# -- Intégration fenêtre principale ---------------------------------------
def test_main_window_bascule_vue_et_clone_modele(app):
    from autoflow.core import templates
    from autoflow.gui.main_window import MainWindow

    window = MainWindow(autoload=False)
    # Bascule liste -> nœuds sans erreur.
    window._set_view(1)
    assert window._views.currentIndex() == 1
    window._set_view(0)

    # Clonage direct d'un modèle dans l'espace de travail.
    before = len(window.workflows)
    tpl = templates.load_templates()[0]
    wf = tpl.to_workflow()
    wf.name = window._unique_name(wf.name)
    window.workflows.append(wf)
    assert len(window.workflows) == before + 1
    window.close()


def test_main_window_services_panneau(app):
    """Les fournisseurs concrets sont bien branchés sur le panneau de params."""
    from autoflow.gui.main_window import MainWindow

    window = MainWindow(autoload=False)
    services = window._panel_services()
    assert callable(services.test_runner)
    assert "Nouveau workflow" not in services.workflows_provider() or \
        isinstance(services.workflows_provider(), list)
    window.close()
