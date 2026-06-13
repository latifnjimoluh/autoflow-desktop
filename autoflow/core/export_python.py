"""Export d'un workflow en script Python autonome (pyautogui/pygetwindow).

Le script généré est **indépendant de l'application** : il s'exécute directement
avec Python + pyautogui, refermant la boucle avec les scripts d'origine de
l'utilisateur. Le résultat est garanti syntaxiquement valide.
"""

from __future__ import annotations

from pathlib import Path

from ..models.workflow import Workflow
from .actions.base import Action

_HEADER = '''"""Script autonome généré par AutoFlow — reproduit le workflow {name!r}.

Dépendances : pip install pyautogui pygetwindow
Exécution :  python {filename}
"""

import time

import pyautogui

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def activer_fenetre(titre, correspondance="contains"):
    """Active une fenêtre par son titre."""
    if gw is None:
        return False
    for fenetre in gw.getAllWindows():
        texte = fenetre.title or ""
        ok = (titre == texte) if correspondance == "exact" else (titre.lower() in texte.lower())
        if texte and ok:
            try:
                fenetre.activate()
            except Exception:
                pass
            return True
    return False


def executer_sequence():
    """Exécute une fois la séquence d'actions du workflow."""
'''

_FOOTER = '''

def main():
    {loop_body}


if __name__ == "__main__":
    main()
'''


def _action_lines(action: Action) -> list[str]:
    """Traduit une action en lignes de code Python (indentées de 4 espaces)."""
    p = action.params
    t = action.type_name
    lines: list[str] = []

    if t == "click":
        if p.get("use_current"):
            lines.append(f"pyautogui.click(button={p.get('button','left')!r}, clicks={int(p.get('clicks',1))})")
        else:
            lines.append(f"pyautogui.click(x={int(p.get('x',0))}, y={int(p.get('y',0))}, "
                         f"button={p.get('button','left')!r}, clicks={int(p.get('clicks',1))})")
    elif t == "move_mouse":
        lines.append(f"pyautogui.moveTo({int(p.get('x',0))}, {int(p.get('y',0))}, duration={float(p.get('duration',0))})")
    elif t == "drag":
        lines.append(f"pyautogui.moveTo({int(p.get('x1',0))}, {int(p.get('y1',0))})")
        lines.append(f"pyautogui.dragTo({int(p.get('x2',0))}, {int(p.get('y2',0))}, "
                     f"duration={float(p.get('duration',0.5))}, button={p.get('button','left')!r})")
    elif t == "scroll":
        lines.append(f"pyautogui.scroll({int(p.get('amount',0))})")
    elif t == "key_press":
        lines.append(f"pyautogui.press({str(p.get('key','enter')).lower()!r}, "
                     f"presses={int(p.get('presses',1))}, interval={float(p.get('interval',0))})")
    elif t == "hotkey":
        keys = p.get("keys", [])
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.replace(",", "+").split("+") if k.strip()]
        args = ", ".join(repr(str(k).lower()) for k in keys)
        lines.append(f"pyautogui.hotkey({args})")
    elif t == "type_text":
        lines.append(f"pyautogui.typewrite({str(p.get('text',''))!r}, interval={float(p.get('interval',0))})")
    elif t == "wait":
        lines.append(f"time.sleep({float(p.get('seconds',0))})")
    elif t == "activate_window":
        lines.append(f"activer_fenetre({str(p.get('title',''))!r}, {str(p.get('match','contains'))!r})")
    elif t == "launch_app":
        lines.append("import os")
        lines.append(f"os.startfile({str(p.get('path',''))!r})  # Windows")
    elif t == "screenshot":
        lines.append(f"pyautogui.screenshot({str(p.get('path','capture.png'))!r})")
    else:
        lines.append(f"pass  # action {t!r} non exportable en script autonome")

    delay = float(getattr(action, "delay_after", 0.0) or 0.0)
    if delay > 0:
        lines.append(f"time.sleep({delay})")
    return lines


def _loop_body(workflow: Workflow) -> str:
    """Génère le corps de ``main`` selon le planning du workflow."""
    sched = workflow.schedule
    if sched.mode == "loop_interval":
        if sched.max_iterations and sched.max_iterations > 0:
            return (f"for _ in range({int(sched.max_iterations)}):\n"
                    f"        executer_sequence()\n"
                    f"        time.sleep({float(sched.interval_seconds)})")
        return ("while True:\n"
                "        executer_sequence()\n"
                f"        time.sleep({float(sched.interval_seconds)})")
    if sched.mode == "repeat_n":
        return (f"for _ in range({max(1, int(sched.max_iterations or 1))}):\n"
                "        executer_sequence()")
    return "executer_sequence()"


def generate_script(workflow: Workflow, filename: str = "workflow.py") -> str:
    """Génère le code source Python autonome reproduisant ``workflow``."""
    header = _HEADER.format(name=workflow.name, filename=filename)
    body_lines: list[str] = []
    for action in workflow.actions:
        if not action.enabled:
            continue
        body_lines.append(f"    # {action.summary()}")
        for line in _action_lines(action):
            body_lines.append(f"    {line}")
    if not body_lines:
        body_lines.append("    pass")
    footer = _FOOTER.format(loop_body=_loop_body(workflow))
    return header + "\n".join(body_lines) + footer


def export_to_file(workflow: Workflow, path: str | Path) -> Path:
    """Écrit le script Python autonome dans ``path``."""
    path = Path(path)
    path.write_text(generate_script(workflow, path.name), encoding="utf-8")
    return path
