"""Point d'entrée d'AutoFlow : lance l'application graphique."""

from __future__ import annotations

import sys


def main() -> int:
    """Crée la QApplication, affiche la fenêtre principale et lance la boucle."""
    from PySide6.QtWidgets import QApplication

    from .gui.main_window import MainWindow
    from .gui.theme import apply_theme
    from .settings import load_settings
    from .utils.logging_setup import setup_logging

    setup_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("AutoFlow")
    # Empêche la fermeture de l'app quand la fenêtre est réduite dans le tray.
    app.setQuitOnLastWindowClosed(False)
    apply_theme(app, load_settings().theme)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
