# ROADMAP — AutoFlow

> Application desktop d'automatisation visuelle du PC (clics, frappes clavier,
> gestion de fenêtres, séquences planifiées). Généralisation visuelle de deux
> scripts Python existants (anti-veille Bloc-notes & automatisation Cmder).

## 1. Vision produit

AutoFlow permet à un utilisateur **non-programmeur** d'assembler visuellement des
**workflows** (séquences d'actions) ciblant des fenêtres Windows par leur titre,
puis de les **planifier** (intervalle, heure, N répétitions, raccourci global),
les **sauvegarder/charger** et les **exécuter** sans geler l'interface, avec une
**console de logs** horodatée et un **arrêt d'urgence**.

Le schéma métier commun aux deux scripts d'origine — *cibler une fenêtre par
titre → la mettre au premier plan → enchaîner des actions clavier/souris →
répéter selon un planning* — devient générique et extensible.

## 2. Choix techniques

| Domaine | Choix | Justification |
|---|---|---|
| Langage | Python 3.11+ (dév sur 3.14) | imposé |
| GUI | PySide6 (Qt) | rendu pro, vues liste/arbre, signaux/threads |
| Souris/clavier | pyautogui | standard, failsafe intégré |
| Fenêtres | pygetwindow + ctypes | énumération + technique foreground Windows |
| Écoute globale | pynput | arrêt d'urgence + enregistrement |
| Persistance | JSON + platformdirs | portable, lisible, repli `~/.autoflow` |
| Tests | pytest + pytest-mock + pytest-qt | cœur mockable + smoke GUI offscreen |
| Packaging | pyinstaller (optionnel) | exécutable Windows |

## 3. Architecture

Séparation stricte **cœur métier** (testable, sans écran) / **interface**.

- `core/actions/` : une classe par action, schéma de paramètres auto-décrit.
- `core/registry.py` : registre/fabrique d'actions (extensibilité).
- `core/executor.py` : moteur séquentiel en thread, pause/arrêt via `Event`,
  signaux Qt pour logs/statut.
- `core/scheduler.py` : modes de planification (`run_once`, `loop_interval`,
  `repeat_n`, `at_time`, `hotkey_trigger`).
- `core/windows_backend.py` : gestion fenêtres, **technique foreground ctypes**
  (simulation Alt) reprise du script B, repli propre hors Windows.
- `input_backend.py` : façade mockable autour de pyautogui (imports paresseux).
- `models/workflow.py` : dataclasses Workflow / Action / Schedule.
- `persistence/store.py` : save/load/import/export JSON.
- `gui/` : fenêtre principale + panneaux, branchés au cœur via signaux.
- `hotkeys.py` / `recorder.py` : écoute globale (pynput).

### Contrainte headless (critique)

`pyautogui`, `pygetwindow`, `pynput` ne sont **jamais importés au niveau module**
dans le code testé : imports **paresseux** dans les fonctions, isolés derrière
`input_backend` / `windows_backend`. Les tests **mockent** ces backends — aucun
test ne bouge réellement la souris. Smoke GUI avec `QT_QPA_PLATFORM=offscreen`.

## 4. Modèle de données

Workflow = `name` + `description` + `schedule` + liste ordonnée d'`actions`.
Action = `type` + `params` + `enabled` + `delay_after`. `max_iterations: 0` = infini.

## 5. Phases & tâches

### Phase 0 — Amorçage
- [x] Vérifier l'environnement (Python, git, gh)
- [x] `venv`, `requirements.txt`, `pyproject.toml`, `.gitignore`, `LICENSE`
- [x] `ROADMAP.md`

### Phase 1 — Cœur métier
- [x] `models/workflow.py` (dataclasses + (de)sérialisation)
- [x] `core/actions/base.py` (Action abstraite + ParamSpec)
- [x] `core/registry.py` (registre/fabrique)
- [x] Actions core (click, move_mouse, drag, scroll, key_press, hotkey,
      type_text, wait, activate_window, launch_app, wait_for_window, screenshot)
- [x] `input_backend.py` (façade pyautogui mockable)
- [x] `core/windows_backend.py` (foreground ctypes + repli)
- [x] `core/executor.py` (thread, pause/arrêt, gestion erreurs)
- [x] `core/scheduler.py` (modes de planification)
- [x] `persistence/store.py` (JSON save/load/import/export)
- [x] Tests unitaires au fil de l'eau

### Phase 2 — Interface
- [x] `gui/main_window.py` + panneaux (liste, éditeur, paramètres, planning)
- [x] `gui/log_console.py`, `gui/coordinate_picker.py`
- [x] Barre de contrôle Démarrer/Pause/Arrêter, signaux thread-safe
- [x] Smoke test GUI offscreen

### Phase 3 — Avancé (si core stable)
- [x] `hotkeys.py` (arrêt d'urgence global)
- [x] `recorder.py` (enregistrement pynput)
- [x] Actions image (`wait_for_image`, `click_image`)
- [x] Workflows d'exemple préchargés
- [ ] Packaging pyinstaller (documenté, optionnel)

### Phase 4 — Finalisation
- [x] `README.md` (FR : installation, lancement, usage)
- [x] Exécution complète `pytest` → vert
- [x] Smoke GUI offscreen vert
- [x] Commits conventionnels + push GitHub (ou instructions)

## 6. Hypothèses prises (sans demander)

1. **Racine projet = `D:\RPA`** ; package Python = `D:\RPA\autoflow`.
2. **Python 3.14** est la seule version disponible : utilisée (≥3.11 respecté).
3. **`gh` absent** : commits locaux faits, instructions de push fournies.
4. Raccourci d'arrêt d'urgence par défaut : **`Ctrl+Shift+Q`**.
5. Données utilisateur dans `platformdirs.user_data_dir("AutoFlow")`,
   repli `~/.autoflow`.
6. Les workflows d'exemple sont copiés dans le dossier de données au premier
   lancement s'il est vide.
7. `force_foreground` n'agit réellement que sur Windows ; ailleurs, repli logué.
8. Les libellés d'interface et docstrings sont en **français** ; les noms de
   symboles et messages de commit en **anglais** (conventional commits).

---

## 7. Extension v2 — Packaging + 20 fonctionnalités

### 7.1 Packaging (application installable)

Transformer le code Python en **application Windows installable** :
- `packaging/autoflow.spec` : build **PyInstaller** (`AutoFlow.exe`, mode fenêtré, onefile).
- `packaging/installer.iss` : **Inno Setup** → installeur, raccourcis menu Démarrer/Bureau,
  désinstalleur, option démarrage automatique.
- `packaging/build.ps1` : script de build de bout en bout.
- README : section « Installation pour utilisateur final » + procédure de build.

### 7.2 Nouvelles dépendances

| Lib | Usage | Note |
|---|---|---|
| `opencv-python` | reconnaissance d'image robuste | import paresseux, dégradation propre |
| `APScheduler` | planification cron/jours/multi-horaires | en mémoire, sans serveur |
| `pytesseract` | OCR | nécessite le binaire **Tesseract** (chemin configurable) |
| `sqlite3` | historique/stats | **inclus** dans Python, aucun serveur/Docker |
| `winreg` | démarrage auto Windows | **inclus** dans Python |
| Qt natif | notifications, presse-papiers, tray | aucune dépendance ajoutée |

### 7.3 Évolution d'architecture

Le workflow passe d'une **liste plate** à une **structure à contrôle de flux**
(actions imbriquées). Le moteur expose dans le `context` : `variables`
(magasin), `run_actions(actions)` (exécute des enfants), `inputs`, `windows`,
`settings`. **Compatibilité ascendante** : un ancien JSON plat se charge et
s'exécute sans modification (champs nouveaux = valeurs par défaut).

### 7.4 Les 20 fonctionnalités (ordre d'implémentation)

- [x] 3. Variables & expressions (`{{var}}`, builtins date/heure/iteration) — *socle*
- [x] 1. Action conditionnelle `condition` (si/sinon, tests variés)
- [x] 2. Boucle/bloc `loop` (N fois / while / until + garde-fou)
- [x] 4. Sous-workflows `run_workflow` (+ anti-récursion)
- [x] 8. `run_command` (subprocess, capture sortie → variable)
- [x] 9. Presse-papiers `clipboard_set/get/paste` (QClipboard)
- [x] 10. Délais aléatoires & jitter « humain »
- [x] 5. Vision OpenCV `find_image`/`wait_for_image`/`click_image`
- [x] 6. Pixel `wait_for_pixel` / test `pixel_color`
- [x] 7. OCR `read_text` (Tesseract, dégradation propre)
- [x] 11. Raccourci global par workflow
- [x] 12. Planification avancée (APScheduler, vue planifications)
- [x] 13. Timeout & retry par action
- [x] 14. Mode pas-à-pas / débogage
- [x] 15. Icône system tray + arrière-plan
- [x] 16. Notifications de bureau
- [x] 17. Démarrage automatique Windows (winreg)
- [x] 18. Historique & stats SQLite + export CSV
- [x] 19. Export d'un workflow en script Python autonome
- [x] 20. Profils / espaces de travail
- [x] Transversal : panneau de réglages (Tesseract, thème clair/sombre, langue FR/EN,
      notifications, démarrage auto), persistant en JSON.
- [x] Packaging : PyInstaller (`AutoFlow.exe`) + Inno Setup (installeur).

### 7.5 Hypothèses v2

1. **opencv/OCR optionnels** : import paresseux ; absence = action ignorée avec
   message clair, jamais de crash (tests inclus).
2. **Démarrage auto** via clé de registre `HKCU\...\Run` (winreg).
3. **Notifications/tray** via Qt natif (pas de dépendance supplémentaire).
4. **Profils** stockés en sous-dossiers JSON du dossier de données.
5. **i18n** par dictionnaire interne FR/EN (plus simple et testable que les `.qm`).
