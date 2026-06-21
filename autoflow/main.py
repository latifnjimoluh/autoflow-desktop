"""Point d'entrée d'AutoFlow : lance l'application graphique."""

from __future__ import annotations

import sys


def main() -> int:
    """Crée la QApplication, affiche la fenêtre principale et lance la boucle."""
    from PySide6.QtWidgets import QApplication

    from autoflow.gui.main_window import MainWindow
    from autoflow.gui.theme import apply_theme
    from autoflow.settings import load_settings
    from autoflow.ui.branding import app_icon
    from autoflow.ui.theme import load_embedded_fonts
    from autoflow.utils.logging_setup import setup_logging

    setup_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("AutoFlow")
    # Empêche la fermeture de l'app quand la fenêtre est réduite dans le tray.
    app.setQuitOnLastWindowClosed(False)
    load_embedded_fonts()
    icon = app_icon(256)
    if icon is not None:
        app.setWindowIcon(icon)
    apply_theme(app, load_settings().theme)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
