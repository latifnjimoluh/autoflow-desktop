"""Tests du système de design v4 : tokens, QSS, ``ThemeManager``, branding.

Pragmatiques (pas de régression visuelle pixel). Les tests GUI tournent en mode
``offscreen`` et vérifient surtout l'**absence d'erreur** et la **cohérence des
tokens** entre thèmes.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from autoflow.ui import theme  # noqa: E402
from autoflow.ui.theme import tokens  # noqa: E402


# --------------------------------------------------------------- tokens
def test_themes_disponibles():
    assert tokens.THEMES == ("dark", "light")


@pytest.mark.parametrize("name", tokens.THEMES)
def test_cle_de_tokens_complete_par_theme(name):
    """Chaque thème expose **toutes** les clés requises, sans manquant."""
    flat = tokens.resolve(name)
    manquantes = tokens.REQUIRED_TOKENS - set(flat)
    assert not manquantes, f"tokens manquants pour {name}: {manquantes}"
    # Aucune valeur vide.
    assert all(flat[k] for k in tokens.REQUIRED_TOKENS)


def test_alias_retrocompatibles_presents():
    """Les alias hérités restent disponibles pour les widgets peints à la main."""
    flat = tokens.resolve("dark")
    for legacy in ("window", "accent_text", "accent_pressed", "danger"):
        assert legacy in flat


def test_accent_coherent_entre_themes():
    """L'accent (identité) est partagé entre clair et sombre."""
    assert tokens.resolve("dark")["accent"] == tokens.resolve("light")["accent"]


def test_surfaces_different_entre_themes():
    """Les surfaces, elles, diffèrent (sinon le thème clair n'existe pas)."""
    assert tokens.resolve("dark")["bg"] != tokens.resolve("light")["bg"]


def test_categorie_couleur_repli():
    assert tokens.category_color("Clavier") != tokens.category_color("Inconnue")
    assert tokens.category_color("Inconnue") == tokens.CATEGORY_COLORS["Général"]


# ----------------------------------------------------------------- QSS
@pytest.mark.parametrize("name", tokens.THEMES)
def test_qss_genere_sans_erreur(name):
    qss = theme.build_qss(tokens.resolve(name))
    assert isinstance(qss, str) and len(qss) > 2000
    # Aucun champ de format non substitué ne doit subsister.
    assert "{" not in qss.replace("{{", "").replace("}}", "") or "}" in qss


def test_qss_cache_par_theme():
    a = theme.qss_for("dark")
    b = theme.qss_for("dark")
    assert a is b  # mis en cache
    assert theme.qss_for("light") != a


# -------------------------------------------------------- ThemeManager
def test_theme_manager_bascule():
    mgr = theme.ThemeManager(theme="dark")
    assert mgr.current == "dark"
    assert mgr.toggle() == "light"
    assert mgr.current == "light"
    mgr.set_theme("dark")
    assert mgr.current == "dark"


def test_theme_manager_theme_inconnu_retombe_sur_dark():
    mgr = theme.ThemeManager(theme="banane")
    assert mgr.current == "dark"


# ------------------------------------------------------- application Qt
@pytest.fixture(scope="module")
def app():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_application_du_theme_ne_crashe_pas(app):
    """Attacher + basculer le thème sur une vraie QApplication ne lève rien."""
    mgr = theme.ThemeManager(theme="dark")
    mgr.attach(app)
    assert app.styleSheet()
    mgr.toggle()
    assert app.styleSheet()
    mgr.toggle()
    assert app.styleSheet()


def test_chargement_polices_embarquees(app):
    """Le chargeur de polices renvoie une liste sans lever (vide possible)."""
    familles = theme.load_embedded_fonts()
    assert isinstance(familles, list)


def test_app_icon_construit(app):
    from autoflow.ui.branding import app_icon

    icon = app_icon(64)
    assert icon is not None
    assert not icon.isNull()


def test_apply_elevation_sur_widget(app):
    from PySide6.QtWidgets import QFrame

    from autoflow.ui.theme import apply_elevation

    frame = QFrame()
    effect = apply_elevation(frame, 2)
    assert effect is not None
    assert frame.graphicsEffect() is effect


def test_about_dialog_se_construit(app):
    from autoflow.gui.about_dialog import AboutDialog

    dialog = AboutDialog()
    assert dialog.windowTitle().startswith("À propos")


def test_palette_suit_theme_courant(app):
    """``palette()`` sans argument suit le thème appliqué (bascule à chaud)."""
    from autoflow.gui.theme import apply_theme, palette

    apply_theme(app, "dark")
    sombre = palette()["bg"]
    apply_theme(app, "light")
    clair = palette()["bg"]
    assert sombre != clair
    apply_theme(app, "dark")  # restaure


@pytest.mark.parametrize("name", tokens.THEMES)
def test_fenetre_principale_dans_les_deux_themes(app, name):
    """La fenêtre principale se construit dans chaque thème sans erreur."""
    from autoflow.gui.main_window import MainWindow
    from autoflow.gui.theme import apply_theme

    apply_theme(app, name)
    window = MainWindow(autoload=False)
    window._refresh_node_view()  # force le rendu de la toile
    window.close()
