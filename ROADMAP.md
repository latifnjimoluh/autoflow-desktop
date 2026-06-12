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

---

## 8. UX no-code v3 — « façon n8n » & configuration concrète des actions

> **Principe directeur : rien ne doit être abstrait.** Partout où l'utilisateur
> doit fournir une information, le champ texte « nu » est remplacé par le
> composant le plus concret possible (capture de touche, liste des fenêtres
> ouvertes, navigateur d'applications, sélecteur de position/région/pixel,
> sélecteur de couleur, etc.). Objectif : une expérience accessible à un
> utilisateur **non technique**, dans l'esprit de **n8n**.

### 8.1 Axes

1. **Configuration concrète des actions** (Phase 1 — prioritaire).
2. **Galerie de modèles** riche, catégorisée, cherchable (Phase 2).
3. **Expérience no-code n8n** : palette, vue en nœuds, onboarding/assistant (Phase 3).

### 8.2 Choix techniques

| Besoin | Choix | Justification |
|---|---|---|
| Types de champ concrets | extension de `ParamSpec` (`key`, `hotkey`, `window`, `app`, `color`, `variable`, `folder`, `workflow` + `placeholder`, `supports_vars`, `depends_on`) | rétro-compatible : les anciens types restent valides, un type inconnu retombe sur un champ texte |
| Services sous-jacents | nouveau paquet `autoflow/services/` (énum. fenêtres, détection apps, capture touches, exécuteur « tester ») | **mockables et testés sans écran** (imports paresseux) |
| Widgets guidés | `ParamPanel` reçoit des *providers* optionnels (fenêtres, apps, variables, workflows, test-runner) | `ParamPanel()` sans argument reste valide (compat tests) |
| Boutons de capture | position / région / pixel injectés au niveau du panneau selon les noms de paramètres | aucune modification du modèle de données |
| Galerie de modèles | JSON dans `examples/templates/` + module `core/templates.py` (métadonnées `category`/`icon`) | format workflow inchangé ; `ensure_examples` conserve son comportement (2 exemples racine) |
| Vue en nœuds | `QGraphicsView` — flux vertical structuré (cartes arrondies, connecteurs, branches Alors/Sinon, boutons « + ») | n8n-like, lisible ; **conserve le modèle structuré existant** (pas de graphe libre) |
| Onboarding | écran d'accueil au 1er lancement + assistant (wizard) | guidage pas-à-pas + accès galerie |

### 8.3 Compatibilité ascendante (garantie, testée)

- `ParamSpec` gagne des champs **optionnels** → tout schéma existant reste valide.
- Les nouveaux types de champ ont un **repli** sur champ texte/`str`.
- Le format JSON des workflows est **inchangé** (les modèles ajoutent seulement
  des clés de métadonnées ignorées par `Workflow.from_dict`).
- Un test dédié charge un **ancien workflow « plat »** et vérifie son exécution.

### 8.4 Phases & Definition of Done

- **Phase 1** : composants concrets §3 + services §4, testés. ✅ cœur non négociable.
- **Phase 2** : galerie de modèles (~15+), vue galerie cherchable, « Utiliser ce modèle ».
- **Phase 3** : palette cherchable + vue en nœuds + onboarding/assistant.

DoD : chaque catégorie d'action configurable via composants concrets ; galerie
riche fonctionnelle ; expérience no-code lisible par un non-technicien ; compat.
ascendante vérifiée par test ; `pytest` vert + smoke GUI offscreen ; commits
atomiques poussés ; rapport final.

### 8.5 Hypothèses v3

1. **Capture de touches/fenêtres en direct** nécessite un affichage : la *logique*
   (mapping touches, énumération) est isolée dans `services/` et testée par mock ;
   les widgets ne sont que des smoke tests offscreen.
2. **Détection des applications** : sous Windows, scan des raccourcis du menu
   Démarrer + chemins courants ; hors Windows, repli sur quelques exécutables du
   `PATH`. Fonction paramétrable (racines injectables) pour les tests.
3. **Vue en nœuds** : disposition en **flux vertical** (pas un graphe libre
   arbitraire), pour rester lisible et cohérente avec le modèle de données.
