"""Tests de l'export d'un workflow en script Python autonome."""

from __future__ import annotations

import ast

from autoflow.core import registry
from autoflow.core.export_python import export_to_file, generate_script
from autoflow.models.workflow import Schedule, Workflow


def sample():
    return Workflow(
        name="Démo export",
        schedule=Schedule(mode="loop_interval", interval_seconds=900, max_iterations=0),
        actions=[
            registry.create_action("activate_window", params={"title": "Bloc-notes"}, delay_after=0.3),
            registry.create_action("hotkey", params={"keys": ["ctrl", "end"]}),
            registry.create_action("type_text", params={"text": "."}),
            registry.create_action("click", params={"x": 10, "y": 20, "clicks": 2}),
            registry.create_action("wait", params={"seconds": 1.5}),
        ],
    )


def test_script_genere_est_valide_syntaxiquement():
    code = generate_script(sample())
    # Ne doit pas lever : le script est syntaxiquement correct.
    ast.parse(code)


def test_script_contient_les_appels_attendus():
    code = generate_script(sample())
    assert "pyautogui.hotkey('ctrl', 'end')" in code
    assert "pyautogui.typewrite('.'" in code
    assert "pyautogui.click(x=10, y=20" in code
    assert "time.sleep(1.5)" in code
    assert "while True:" in code  # boucle infinie loop_interval


def test_action_non_exportable_reste_valide():
    wf = Workflow(name="X", actions=[registry.create_action("read_text")])
    code = generate_script(wf)
    ast.parse(code)
    assert "non exportable" in code


def test_export_to_file(tmp_path):
    chemin = export_to_file(sample(), tmp_path / "out.py")
    assert chemin.exists()
    ast.parse(chemin.read_text(encoding="utf-8"))


def test_repeat_n_genere_boucle_bornee():
    wf = Workflow(name="R", schedule=Schedule(mode="repeat_n", max_iterations=4),
                  actions=[registry.create_action("wait", params={"seconds": 0.1})])
    code = generate_script(wf)
    ast.parse(code)
    assert "for _ in range(4)" in code
