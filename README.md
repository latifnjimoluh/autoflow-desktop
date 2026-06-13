# AutoFlow

**AutoFlow** est une application desktop d'automatisation visuelle du PC. Elle
permet à un utilisateur **non-programmeur** de composer des **séquences
d'actions** (clics, frappes clavier, raccourcis, gestion de fenêtres, attentes…)
et de les **planifier**, sans écrire la moindre ligne de code.

C'est la généralisation visuelle et extensible de deux scripts d'origine :

- **Anti-veille** : tape périodiquement dans le Bloc-notes pour empêcher la mise
  en veille.
- **Automatisation Cmder** : force Cmder au premier plan et relance `continue`
  toutes les 30 minutes.

Ces deux scripts sont fournis comme **workflows d'exemple** préchargés au premier
lancement.

---

## Fonctionnalités

- 🧩 **Composition visuelle** de workflows par assemblage de briques d'actions.
- 🎯 **Ciblage de fenêtres par titre** (`contains` / `exact`) avec passage au
  premier plan, y compris la **technique Windows** (simulation Alt) qui contourne
  le « Access Denied » de `SetForegroundWindow`.
- ⏱️ **Planification** : une fois, en boucle (intervalle), N répétitions, à une
  heure précise, ou déclenchée par raccourci global.
- 💾 **Sauvegarde / chargement / import / export** au format JSON.
- ▶️ **Démarrer / Pause / Arrêter**, exécution dans un **thread de fond**
  (l'interface ne gèle jamais).
- 🛑 **Arrêt d'urgence** : failsafe `pyautogui` (souris coin haut-gauche) **et**
  raccourci global configurable (`Ctrl+Shift+Q` par défaut).
- 📜 **Console de logs** horodatée.
- 🖱️ **Sélecteur de coordonnées** en temps réel pour configurer les clics.
- 🎥 **Mode enregistrement** et **actions par reconnaissance d'image** (avancé).

## Catalogue d'actions

| Catégorie | Actions |
|---|---|
| Souris | Clic, Déplacer la souris, Glisser-déposer, Défilement |
| Clavier | Appui touche, Raccourci, Taper du texte |
| Fenêtres | Activer une fenêtre, Lancer une application, Attendre une fenêtre |
| Écran | Capture d'écran, Attendre une image, Cliquer sur une image |
| Contrôle | Attente |

Le **registre d'actions** rend l'ajout d'un nouveau type trivial : il suffit
d'écrire une classe décorée par `@register` ; l'interface la découvre seule.

---

## Installation

Prérequis : **Python 3.11+** (développé et testé sous Python 3.14, Windows 10).

```powershell
# 1. Cloner le dépôt puis se placer dedans
cd AutoFlow

# 2. Créer et activer un environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # PowerShell
# source .venv/bin/activate       # Linux / macOS

# 3. Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```powershell
python -m autoflow.main
```

Au premier démarrage, les deux workflows d'exemple sont copiés dans votre dossier
de données utilisateur (`%LOCALAPPDATA%\AutoFlow\workflows` sous Windows, sinon
`~/.autoflow`).

## Utilisation rapide

1. **Panneau gauche** : choisissez ou créez un workflow (*Nouveau*, *Dupliquer*,
   *Supprimer*, *Importer*, *Exporter*).
2. **Panneau central** : ajoutez des actions via *Ajouter une action ▾* (menu par
   catégorie), réordonnez-les, activez/désactivez-les.
3. **Panneau droit** :
   - onglet *Paramètres de l'action* : formulaire généré automatiquement ;
   - onglet *Workflow & planning* : nom, description, mode de planification ;
   - onglet *Coordonnées* : capture de la position de la souris.
4. **Barre d'outils** : *Démarrer / Pause / Arrêter*, réglage du *failsafe*, de la
   pause globale `pyautogui` et du raccourci d'arrêt d'urgence.
5. **Console de logs** (bas) : suivez chaque action horodatée.

> ⚠️ L'automatisation réelle (clics, frappes, fenêtres) nécessite **Windows avec
> un affichage**. Sur Linux/macOS ou en environnement sans écran, le cœur reste
> importable et testable, mais les actions matérielles ne s'exécutent pas.

---

## Architecture

```
autoflow/
├── core/
│   ├── actions/          # une classe par type d'action (+ schéma de paramètres)
│   ├── registry.py       # registre / fabrique d'actions
│   ├── executor.py       # moteur séquentiel (thread, pause/arrêt, signaux)
│   ├── scheduler.py      # logique de planification
│   └── windows_backend.py# gestion des fenêtres (ctypes + repli hors Windows)
├── models/workflow.py    # dataclasses Workflow / Schedule
├── persistence/store.py  # save/load/import/export JSON
├── input_backend.py      # façade pyautogui (import paresseux, mockable)
├── hotkeys.py            # arrêt d'urgence global (pynput)
├── recorder.py          # mode enregistrement (pynput)
├── gui/                 # interface PySide6 (panneaux + thread d'exécution)
└── main.py              # point d'entrée
```

Le **cœur métier** est strictement séparé de l'interface : il n'importe ni
`pyautogui`, ni `pygetwindow`, ni `pynput` au niveau module (imports paresseux),
ce qui le rend **entièrement testable** sans écran.

## Tests

```powershell
# Sous environnement sans affichage, forcer le rendu Qt hors écran :
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest
```

La suite couvre les actions, le moteur, le planificateur, la persistance, le
registre, le backend fenêtres (tous mockés — **aucun test ne bouge la souris**),
ainsi qu'un **smoke test GUI** en mode `offscreen`.

## Packaging (optionnel)

Pour produire un exécutable Windows :

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name AutoFlow -p . autoflow/main.py
```

---

## 🚀 Extension v2 — Application installable + 20 fonctionnalités

### Installer / lancer comme une vraie application (sans Python)

AutoFlow s'empaquette en **exécutable Windows autonome** + **installeur** :

```powershell
# Depuis la racine du dépôt, dans le venv :
pip install pyinstaller
.\packaging\build.ps1
```

- Produit `dist\AutoFlow\AutoFlow.exe` (application autonome, double-clic).
- Si **Inno Setup** ([jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php))
  est installé, produit aussi `dist\AutoFlow-Setup.exe` : un **installeur**
  classique (raccourcis Bureau/menu Démarrer, option démarrage automatique,
  désinstalleur). L'utilisateur final n'a **pas besoin de Python**.

### Nouvelles fonctionnalités (20)

**Logique & intelligence**
1. **Conditions** (`si / sinon`) : fenêtre présente/absente, image, couleur de
   pixel, fichier existant, comparaison de variable.
2. **Boucles** (`N fois` / `tant que` / `jusqu'à`) avec garde-fou anti-infini.
3. **Variables & expressions** : `{{nom}}` dans les paramètres, builtins
   `{{date}}`, `{{heure}}`, `{{iteration}}`, capture OCR/presse-papiers/commande.
4. **Sous-workflows** (`run_workflow`) réutilisables, avec anti-récursion.

**Perception de l'écran**
5. **Reconnaissance d'image** (OpenCV) : `find_image`, `wait_for_image`,
   `click_image` (seuil de confiance).
6. **Pixel** : `wait_for_pixel` et test couleur avec tolérance.
7. **OCR** (`read_text`, Tesseract) — **dégradation propre** si Tesseract absent.

**Nouvelles actions**
8. **Commande / script** (`run_command`) avec capture de sortie en variable.
9. **Presse-papiers** (`clipboard_set/get/paste`).
10. **Délais aléatoires & jitter** « humain ».

**Déclenchement & exécution**
11. **Raccourci global par workflow** (mode « déclenché par raccourci »).
12. **Planification avancée** (cron / jours / horaires multiples, APScheduler).
13. **Timeout & ré-essais par action** (+ comportement en cas d'échec).
14. **Mode pas-à-pas / débogage** avec surlignage et état des variables.

**Intégration système**
15. **Icône barre des tâches** (exécution en arrière-plan, menu contextuel).
16. **Notifications de bureau** (début / fin / erreur).
17. **Démarrage automatique avec Windows** (clé de registre `Run`).

**Données & organisation**
18. **Historique & statistiques** en **SQLite local** (aucun serveur, aucun
    Docker) + **export CSV**.
19. **Export d'un workflow en script Python autonome** (`.py` exécutable seul).
20. **Profils / espaces de travail** (Travail, Jeux…), chacun ses workflows.

**Transversal** : panneau de **réglages** (failsafe, pause, chemin Tesseract,
**thème clair/sombre**, **langue FR/EN**, notifications, démarrage auto).

### Notes importantes

- **SQLite et winreg sont inclus dans Python** : aucun serveur, aucun Docker,
  aucune installation supplémentaire pour l'historique et le démarrage auto.
- **OCR** : nécessite le binaire **Tesseract** installé séparément ; son chemin
  se configure dans *Réglages*. En son absence, l'action OCR est ignorée
  proprement (message clair, pas de plantage).
- **Compatibilité ascendante** : les anciens workflows (format « plat ») se
  chargent et s'exécutent sans modification (vérifié par un test dédié).
- L'automatisation réelle nécessite **Windows avec affichage**.

## Licence

Distribué sous licence **MIT** — voir [LICENSE](LICENSE).
