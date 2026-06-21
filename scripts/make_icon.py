"""Génère ``packaging/app.ico`` à partir du logo peint (hors-ligne).

Utilise Qt pour rendre l'icône à plusieurs tailles et l'enregistrer en ``.ico``.
Best-effort : si l'écriture ICO échoue, enregistre un PNG de repli. À lancer avec
le Python du projet :

    QT_QPA_PLATFORM=offscreen python scripts/make_icon.py
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from autoflow.ui.branding import app_icon  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "packaging" / "app.ico"


def main() -> int:
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    icon = app_icon(256)
    if icon is None:
        print("Qt indisponible — icône non générée.")
        return 1
    pix = icon.pixmap(256, 256)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if pix.save(str(OUT), "ICO"):
        print("écrit", OUT)
        return 0
    # Repli PNG si le greffon ICO est absent.
    png = OUT.with_suffix(".png")
    pix.save(str(png), "PNG")
    print("ICO indisponible, PNG écrit", png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
