"""Génère la galerie de modèles JSON dans examples/templates/.

Script utilitaire exécuté une fois lors de la mise en place de la galerie v3.
Chaque modèle réutilise le format de workflow existant, enrichi de deux clés de
métadonnées (``category`` et ``icon``) ignorées par ``Workflow.from_dict``.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples" / "templates"
OUT.mkdir(parents=True, exist_ok=True)


def sched(mode="run_once", **kw):
    base = {"mode": mode, "interval_seconds": 900, "max_iterations": 0,
            "at_time": "08:00", "hotkey": "ctrl+shift+r"}
    base.update(kw)
    return base


def act(type_name, params, delay_after=0.0, enabled=True, **extra):
    d = {"type": type_name, "params": params, "enabled": enabled,
         "delay_after": delay_after}
    d.update(extra)
    return d


TEMPLATES = [
    # ---- Maintien d'activité -------------------------------------------------
    {
        "name": "Anti-veille — Bloc-notes",
        "description": "Empêche la mise en veille en tapant un point dans le Bloc-notes toutes les 15 minutes.",
        "category": "Maintien d'activité", "icon": "☕",
        "schedule": sched("loop_interval", interval_seconds=900),
        "actions": [
            act("activate_window", {"title": "Bloc-notes", "match": "contains", "force_foreground": False}, 0.3),
            act("hotkey", {"keys": ["ctrl", "end"]}, 0.1),
            act("type_text", {"text": ".", "paste": False, "interval": 0.05}),
        ],
    },
    {
        "name": "Anti-veille — Terminal / Cmder",
        "description": "Garde un terminal actif en envoyant régulièrement la touche Entrée.",
        "category": "Maintien d'activité", "icon": "☕",
        "schedule": sched("loop_interval", interval_seconds=600),
        "actions": [
            act("activate_window", {"title": "Cmder", "match": "contains", "force_foreground": True}, 0.4),
            act("key_press", {"key": "enter", "presses": 1, "interval": 0.0}),
        ],
    },
    {
        "name": "Anti-veille — Bouger la souris discrètement",
        "description": "Déplace légèrement la souris à intervalle régulier, sans dépendre d'une application.",
        "category": "Maintien d'activité", "icon": "☕",
        "schedule": sched("loop_interval", interval_seconds=120),
        "actions": [
            act("move_mouse", {"x": 200, "y": 200, "duration": 0.3}, 0.5),
            act("move_mouse", {"x": 205, "y": 205, "duration": 0.3}),
        ],
    },
    {
        "name": "Anti-veille — Touche neutre F15",
        "description": "Appuie périodiquement sur F15 (touche sans effet) pour simuler une activité.",
        "category": "Maintien d'activité", "icon": "☕",
        "schedule": sched("loop_interval", interval_seconds=180),
        "actions": [
            act("key_press", {"key": "f15", "presses": 1, "interval": 0.0}),
        ],
    },
    # ---- Terminal / Dev ------------------------------------------------------
    {
        "name": "Cmder — relancer « continue »",
        "description": "Force Cmder au premier plan et relance la commande « continue » toutes les 30 minutes.",
        "category": "Terminal / Dev", "icon": "💻",
        "schedule": sched("loop_interval", interval_seconds=1800),
        "actions": [
            act("activate_window", {"title": "Cmder", "match": "contains", "force_foreground": True}, 0.5),
            act("key_press", {"key": "enter", "presses": 2, "interval": 0.2}, 0.2),
            act("type_text", {"text": "continue", "paste": False, "interval": 0.0}, 0.2),
            act("key_press", {"key": "enter", "presses": 1, "interval": 0.0}),
        ],
    },
    {
        "name": "Git — pull périodique d'un dossier",
        "description": "Exécute « git pull » dans un dossier de projet à intervalle régulier.",
        "category": "Terminal / Dev", "icon": "💻",
        "schedule": sched("loop_interval", interval_seconds=3600),
        "actions": [
            act("run_command", {"command": "git pull", "shell": True,
                                "workdir": "", "output_var": "git_resultat", "timeout": 60.0}),
        ],
    },
    {
        "name": "Build — relancer un script planifié",
        "description": "Lance une commande de build à heure fixe (ex. compilation nocturne).",
        "category": "Terminal / Dev", "icon": "💻",
        "schedule": sched("at_time", at_time="02:00"),
        "actions": [
            act("run_command", {"command": "npm run build", "shell": True,
                                "workdir": "", "output_var": "build_log", "timeout": 600.0}),
        ],
    },
    # ---- Productivité --------------------------------------------------------
    {
        "name": "Ouvrir mon espace de travail",
        "description": "Lance d'un coup plusieurs applications de travail au démarrage.",
        "category": "Productivité", "icon": "🚀",
        "schedule": sched("run_once"),
        "actions": [
            act("launch_app", {"path": "notepad.exe", "args": ""}, 1.0),
            act("launch_app", {"path": "calc.exe", "args": ""}, 1.0),
        ],
    },
    {
        "name": "Fermer les distractions",
        "description": "Ferme une liste d'applications distrayantes pour rester concentré.",
        "category": "Productivité", "icon": "🚀",
        "schedule": sched("run_once"),
        "actions": [
            act("run_command", {"command": "taskkill /IM notepad.exe /F", "shell": True,
                                "workdir": "", "output_var": "", "timeout": 15.0}),
        ],
    },
    {
        "name": "Capture d'écran planifiée",
        "description": "Prend une capture d'écran complète à intervalle régulier.",
        "category": "Productivité", "icon": "🚀",
        "schedule": sched("loop_interval", interval_seconds=1800),
        "actions": [
            act("screenshot", {"path": "capture_{{iteration}}.png", "region": False,
                               "x": 0, "y": 0, "width": 0, "height": 0}),
        ],
    },
    {
        "name": "Sauvegarde rapide périodique (Ctrl+S)",
        "description": "Envoie Ctrl+S à intervalle régulier pour sauvegarder le document actif.",
        "category": "Productivité", "icon": "🚀",
        "schedule": sched("loop_interval", interval_seconds=300),
        "actions": [
            act("hotkey", {"keys": ["ctrl", "s"]}),
        ],
    },
    {
        "name": "Rappel d'étirement",
        "description": "Affiche un rappel toutes les heures pour faire une pause et s'étirer.",
        "category": "Productivité", "icon": "🚀",
        "schedule": sched("loop_interval", interval_seconds=3600),
        "actions": [
            act("run_command", {"command": "msg * Faites une pause et etirez-vous !",
                                "shell": True, "workdir": "", "output_var": "", "timeout": 10.0}),
        ],
    },
    # ---- Automatisation répétitive ------------------------------------------
    {
        "name": "Auto-clic configurable",
        "description": "Clique en boucle à une position donnée, à intervalle régulier.",
        "category": "Automatisation répétitive", "icon": "🔁",
        "schedule": sched("run_once"),
        "actions": [
            act("loop", {"mode": "count", "count": 20, "max_iterations": 1000,
                         "test": "window_present", "title": "", "match": "contains",
                         "image_path": "", "confidence": 0.8, "x": 0, "y": 0,
                         "color": "#000000", "tolerance": 10, "file_path": "",
                         "var_name": "", "operator": "==", "value": ""},
                body=[act("click", {"use_current": False, "x": 500, "y": 400,
                                    "button": "left", "clicks": 1}, 0.5)]),
        ],
    },
    {
        "name": "Saisie répétitive et validation",
        "description": "Tape un texte puis valide avec Entrée, en boucle (ex. remplir un champ).",
        "category": "Automatisation répétitive", "icon": "🔁",
        "schedule": sched("run_once"),
        "actions": [
            act("loop", {"mode": "count", "count": 5, "max_iterations": 1000,
                         "test": "window_present", "title": "", "match": "contains",
                         "image_path": "", "confidence": 0.8, "x": 0, "y": 0,
                         "color": "#000000", "tolerance": 10, "file_path": "",
                         "var_name": "", "operator": "==", "value": ""},
                body=[
                    act("type_text", {"text": "Ligne {{iteration}}", "paste": False, "interval": 0.0}, 0.2),
                    act("key_press", {"key": "enter", "presses": 1, "interval": 0.0}, 0.3),
                ]),
        ],
    },
    # ---- Surveillance --------------------------------------------------------
    {
        "name": "Attendre une fenêtre puis agir",
        "description": "Attend l'apparition d'une fenêtre, la met au premier plan puis notifie.",
        "category": "Surveillance", "icon": "👁",
        "schedule": sched("run_once"),
        "actions": [
            act("wait_for_window", {"title": "Calculatrice", "match": "contains", "timeout": 60.0}, 0.2),
            act("activate_window", {"title": "Calculatrice", "match": "contains", "force_foreground": True}, 0.2),
            act("run_command", {"command": "msg * La fenetre est apparue !", "shell": True,
                                "workdir": "", "output_var": "", "timeout": 10.0}),
        ],
    },
    {
        "name": "Attendre une image puis cliquer",
        "description": "Attend qu'une image apparaisse à l'écran puis clique dessus (vision).",
        "category": "Surveillance", "icon": "👁",
        "schedule": sched("run_once"),
        "actions": [
            act("wait_for_image", {"path": "bouton.png", "timeout": 30.0, "confidence": 0.9}, 0.2),
            act("click_image", {"path": "bouton.png", "confidence": 0.9, "button": "left"}),
        ],
    },
    # ---- Média / Présentation -----------------------------------------------
    {
        "name": "Avancer les diapositives",
        "description": "Appuie sur la flèche droite toutes les X secondes pour faire défiler une présentation.",
        "category": "Média / Présentation", "icon": "🎬",
        "schedule": sched("loop_interval", interval_seconds=10),
        "actions": [
            act("key_press", {"key": "right", "presses": 1, "interval": 0.0}),
        ],
    },
    {
        "name": "Commande média — Lecture / Pause",
        "description": "Envoie la touche média Lecture/Pause (utile pour piloter un lecteur).",
        "category": "Média / Présentation", "icon": "🎬",
        "schedule": sched("hotkey_trigger", hotkey="ctrl+shift+p"),
        "actions": [
            act("key_press", {"key": "playpause", "presses": 1, "interval": 0.0}),
        ],
    },
]


def slug(name: str) -> str:
    import re
    s = re.sub(r"[^\w]+", "_", name.lower(), flags=re.UNICODE).strip("_")
    return s or "modele"


def main() -> None:
    for tpl in TEMPLATES:
        path = OUT / f"{slug(tpl['name'])}.json"
        path.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(TEMPLATES)} modèles écrits dans {OUT}")


if __name__ == "__main__":
    main()
