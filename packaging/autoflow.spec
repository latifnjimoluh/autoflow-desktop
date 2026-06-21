# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller d'AutoFlow (build one-folder ``AutoFlow/`` + ``AutoFlow.exe``).

Embarque toutes les ressources nécessaires au fonctionnement hors-ligne :
- ``examples/`` : workflows et modèles préchargés ;
- ``autoflow/ui`` : polices, logo SVG, assets du système de design.

L'icône (``packaging/app.ico``) est utilisée si présente. Le ``.exe`` Windows
réel est produit par la CI (runner ``windows-latest``) ; en local/Linux ce spec
sert de **build de validation**.
"""

import os

_here = os.path.abspath(os.getcwd())
_root = os.path.abspath(os.path.join(_here, ".."))


def _path(*parts):
    return os.path.join(_root, *parts)


# Ressources embarquées : examples + assets non-Python du système de design
# (logo SVG, polices). Chaque dossier n'est ajouté que s'il existe.
_data_pairs = [
    (_path("examples"), "examples"),
    (_path("autoflow", "ui", "assets"), os.path.join("autoflow", "ui", "assets")),
    (_path("autoflow", "ui", "theme", "assets"),
     os.path.join("autoflow", "ui", "theme", "assets")),
]
datas = [(src, dst) for src, dst in _data_pairs if os.path.exists(src)]

_icon = _path("packaging", "app.ico")
icon = _icon if os.path.exists(_icon) else None


a = Analysis(
    [_path("autoflow", "main.py")],
    pathex=[_root],
    binaries=[],
    datas=datas,
    hiddenimports=["autoflow.services.updater", "autoflow.services.version"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoFlow',
)
