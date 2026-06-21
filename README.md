# AutoFlow

[![CI](https://github.com/latifnjimoluh/autoflow-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/latifnjimoluh/autoflow-desktop/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/latifnjimoluh/autoflow-desktop?sort=semver)](https://github.com/latifnjimoluh/autoflow-desktop/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/latifnjimoluh/autoflow-desktop/total)](https://github.com/latifnjimoluh/autoflow-desktop/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**AutoFlow** est une application desktop d'automatisation visuelle du PC. Elle
permet à un utilisateur **non-programmeur** de composer des **séquences
d'actions** (clics, frappes clavier, raccourcis, gestion de fenêtres, attentes…)
et de les **planifier**, sans écrire la moindre ligne de code.

## ⬇️ Télécharger

Récupérez la **dernière version** depuis la page des Releases :

➡️ **[Télécharger AutoFlow pour Windows](https://github.com/latifnjimoluh/autoflow-desktop/releases/latest)**

Téléchargez l'archive `AutoFlow-<version>-windows-x64.zip`, décompressez-la et
lancez `AutoFlow.exe`. Un fichier `.sha256` accompagne chaque artefact pour
vérifier l'intégrité.

> **Avertissement SmartScreen** : l'exécutable n'étant pas signé (la signature de
> code requiert un certificat payant), Windows peut afficher un écran
> « Windows a protégé votre ordinateur ». Cliquez **Informations complémentaires →
> Exécuter quand même**. La signature reste une option documentée, non activée.

## 🔄 Mises à jour intégrées

AutoFlow vérifie automatiquement les nouvelles versions :

- **Au démarrage** (en arrière-plan, sans bloquer l'interface) si l'option
  *« Vérifier les mises à jour au démarrage »* est activée dans **⚙ Réglages**.
- **À la demande** via le bouton **🔄 Mises à jour** de la barre d'outils.

Quand une version plus récente est publiée, une boîte de dialogue présente la
version et ses **notes** avec deux choix : **Télécharger** (ouvre l'asset de la
Release) ou **Installer et redémarrer** (télécharge puis lance l'installeur et
quitte l'app — un `.exe` en cours d'exécution ne pouvant pas être écrasé). La
vérification interroge l'API GitHub via la bibliothèque standard et gère
proprement l'absence de réseau, la limite de débit et les réponses malformées.

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

Pour produire un exécutable Windows à partir du spec versionné :

```powershell
pip install -e ".[packaging]"
python scripts/make_icon.py        # génère packaging/app.ico (optionnel)
cd packaging
pyinstaller --noconfirm --clean autoflow.spec
# -> dist/AutoFlow/AutoFlow.exe (+ ressources embarquées)
```

## 📦 Publier une nouvelle version (mainteneurs)

La publication est **automatisée** par GitHub Actions :

1. Bumpez la version dans `autoflow/__init__.py` (`__version__`, **source unique
   de vérité** — `pyproject.toml` la lit dynamiquement) et ajoutez une entrée
   dans `CHANGELOG.md`.
2. Committez et **poussez sur `main`**. Le workflow `release.yml` compare
   `__version__` au dernier tag : **si la version a augmenté**, il construit
   l'`.exe` sur `windows-latest`, calcule les checksums, **pose le tag
   `v{version}`** et **publie la Release** avec l'archive téléchargeable.
3. Alternative : poussez un tag `vX.Y.Z` manuellement pour forcer une Release.

À chaque `push`/`pull_request` sur `main`, `ci.yml` exécute la suite de tests
(Python 3.11/3.12, mode offscreen) + lint/type-check.

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

## 🎨 Expérience no-code v3 — « façon n8n »

AutoFlow v3 rend l'application **réellement accessible à n'importe qui**, même
sans aucune connaissance technique. Le principe directeur : **rien n'est
abstrait** — chaque réglage devient concret, guidé et précis.

### Configuration concrète des actions (plus de champ « nu »)

À chaque endroit où vous fournissez une information, AutoFlow propose le
composant **le plus concret possible** :

- **Clavier** — *Appui touche* : bouton **« ⌨ Capturer »** qui enregistre la
  vraie touche que vous pressez, **plus** une liste cherchable de toutes les
  touches (lettres, chiffres, F1–F24, flèches, média…). *Raccourci* : capture de
  la combinaison réelle (« Ctrl + Maj + S » affiché en clair) ou interrupteurs de
  modificateurs + touche finale. *Taper du texte* : insertion de variables
  `{{…}}` d'un clic, et option « coller d'un coup ».
- **Souris** — choix **« position actuelle »** ou **« coordonnées précises »**
  avec bouton **« 📍 Capturer une position »** (la position s'affiche en direct).
  Boutons de souris en liste, capture de **départ/arrivée** pour le glisser.
- **Fenêtres** — **liste déroulante des fenêtres ouvertes** (rafraîchissable),
  plus un motif manuel pour les fenêtres pas encore ouvertes. *Lancer une
  application* : **applications installées** (menu Démarrer) / **parcourir** /
  saisie manuelle.
- **Système** — constructeur de commande clair : dossier de travail, capture de
  la sortie dans une **variable**, délai max.
- **Contrôle** — constructeur de **condition** dont les champs s'adaptent au type
  de test choisi ; boucles guidées avec garde-fou.
- **Écran** — sélecteur de couleur visuel, bouton **« 🎨 Capturer un pixel »**,
  capture de **région**.

Chaque action affiche une **aide en langage simple**, des **exemples** en
filigrane, un **résumé en langage naturel** (« Clic gauche à la position
(120, 340) ») et un bouton **« ▶ Tester cette action »** pour voir le résultat
immédiatement.

### Galerie de modèles

Un bouton **« 📚 Galerie de modèles »** ouvre une galerie **catégorisée et
cherchable** de plus de **15 modèles prêts à l'emploi** (maintien d'activité,
terminal/dev, productivité, automatisation répétitive, surveillance,
média/présentation). **« Utiliser ce modèle »** le clone dans vos workflows,
prêt à éditer.

### Vue en nœuds + assistant

- **Vue en nœuds** (bouton **« 🔗 Schéma »**) : le workflow s'affiche comme un
  enchaînement de **cartes** reliées, avec branches *Alors / Sinon*, boutons
  **« + »** d'insertion et **pan/zoom**. Bascule **Liste ⇄ Nœuds** à tout moment.
- **Palette d'actions** cherchable, regroupée par catégorie.
- **Écran d'accueil** au premier lancement + **assistant** guidé (bouton
  **« 🧭 Assistant »**) pour construire un premier workflow pas à pas.

> **Compatibilité ascendante** : le format JSON des workflows est inchangé ; les
> anciens workflows « plats » se chargent et s'exécutent sans modification
> (vérifié par un test dédié).

## 🎨 Design visuel v4 — système de design & thèmes

AutoFlow s'appuie sur un **système de design à tokens** (source unique de
vérité, `autoflow/ui/theme/`) : **aucune couleur n'est codée en dur** dans les
widgets, tout dérive des tokens. Le résultat vise un produit **moderne, calme et
cohérent**, entre la toile à nœuds de **n8n** et le minimalisme de
**Linear / Raycast**.

- **Identité** : une seule couleur d'accent affirmée — **indigo `#6D5EF0`** —,
  géométrie arrondie, espaces généreux (base 8), élévation douce.
- **Deux thèmes complets** (sombre par défaut + clair tout aussi abouti),
  **basculables à chaud** via le bouton **🌓 Thème** de la barre d'outils (le
  choix est persisté ; réglable aussi dans **⚙ Réglages**). Toute l'app suit la
  bascule, y compris la **toile à nœuds** et la **console de logs** monospace.
- **Composants soignés** dans tous leurs états (normal / survol / focus / actif /
  désactivé) : boutons (primaire, fantôme, danger), champs avec focus à l'accent
  et état d'erreur, listes, onglets, menus, barres de défilement fines, infobulles.
- **Toile à nœuds** : cartes à **liseré de couleur par catégorie**, **pastille
  d'état**, connecteurs en courbes, **fond quadrillé** discret, pan/zoom.
- **Accessibilité** : focus clavier visible ; les états sémantiques ne reposent
  **jamais sur la seule couleur** (glyphe + libellé) — sûr pour le daltonisme.
- **Identité applicative** : icône peinte (fenêtre + barre des tâches) et fenêtre
  **ℹ À propos** (version, lien dépôt).

> **Polices** : Inter (interface) et JetBrains Mono (logs) sont chargées si
> présentes dans `autoflow/ui/theme/assets/fonts/` (100 % hors-ligne) ; sinon
> repli automatique sur `Segoe UI` / `Consolas`.
>
> **Captures** : `QT_QPA_PLATFORM=offscreen python scripts/capture_screens.py`
> génère des aperçus des deux thèmes dans `docs/images/`.

## ⚡ Lot 2 — automatisation réactive, données & robustesse (20 nouveautés)

> **Aucun serveur ni Docker** : tout repose sur du **JSON**, **SQLite intégré**
> et un **coffre de secrets chiffré localement** (`cryptography`). Chaque
> nouveauté garde la philosophie no-code (configuration concrète, résumé en
> langage naturel) et **étend** le format de workflow sans casser l'existant
> (anciens workflows toujours chargeables — vérifié par test).

**Déclencheurs événementiels** (bouton **⚡ Déclencheurs**) — un workflow démarre
sur événement, en plus de la planification :
- **Fenêtre** (apparition / fermeture / focus), **fichier/dossier** (`watchdog`),
  **presse-papiers** (avec regex), **inactivité** (idle Windows), **webhook**
  (serveur HTTP local). Le contexte (fichier, contenu, corps JSON…) est injecté
  en variables dans le workflow.

**Données (façon n8n)** :
- **Boucle « pour chaque »** (liste/variable, lignes CSV/Excel, fichiers d'un
  dossier) avec `item`/`index` ; **lire/écrire CSV & Excel** ; **requête HTTP/API**
  (GET/POST/PUT/DELETE, extraction d'un champ JSON) ; **texte** (regex, découpe,
  casse…) et **calcul** mathématique sécurisé ; **variables globales** + **coffre
  de secrets** chiffré.

**Robustesse & actions** :
- **Ciblage d'éléments d'interface** Windows (`pywinauto`), **bloc try / en cas
  d'erreur**, **conditions composées ET/OU**, **file d'attente / exécution
  exclusive** ; actions **fichiers/dossiers**, **e-mail (SMTP)** avec pièce jointe,
  **son & synthèse vocale** (`pyttsx3`), **saisie utilisateur** en cours
  d'exécution, **alimentation/volume** (avec confirmation pour éteindre/redémarrer).

**Vue** : **tableau de bord** (📊, statistiques, taux de succès, activité récente)
et **palette de commandes** (**Ctrl+K**) pour lancer un workflow en deux frappes.

> **Fonctions Windows** (ciblage UI, voix, contrôle système, inactivité) :
> **dégradation propre** sur les autres OS (message clair, jamais de crash). Les
> dépendances Windows optionnelles s'installent via `pip install -e ".[windows]"`.

## Licence

Distribué sous licence **MIT** — voir [LICENSE](LICENSE).
