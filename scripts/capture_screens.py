"""Capture des captures d'écran de la fenêtre principale (clair + sombre).

Rendu **hors écran** (``QT_QPA_PLATFORM=offscreen``) vers ``docs/images/``.
Sert à documenter le système de design v4 dans le README. À lancer avec le
Python du projet :

    QT_QPA_PLATFORM=offscreen python scripts/capture_screens.py
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from autoflow.gui.main_window import MainWindow  # noqa: E402
from autoflow.gui.theme import apply_theme  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "images"


def _shot(app: QApplication, theme: str) -> Path:
    apply_theme(app, theme)
    window = MainWindow(autoload=False)
    window.resize(1180, 760)
    window._add_action("activate_window")
    window._add_action("type_text")
    window._add_action("click")
    window.show()
    app.processEvents()
    pix = window.grab()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"autoflow-{theme}.png"
    pix.save(str(path))
    window.close()
    return path


def main() -> int:
    app = QApplication.instance() or QApplication([])
    for theme in ("dark", "light"):
        path = _shot(app, theme)
        print("écrit", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
