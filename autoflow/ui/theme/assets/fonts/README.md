# Polices embarquées

Déposez ici les fichiers de police pour un rendu **identique sur toutes les
machines** (fonctionnement 100 % hors-ligne) :

- **Inter** — police d'interface : `Inter-Regular.ttf`, `Inter-Medium.ttf`,
  `Inter-SemiBold.ttf` (https://rsms.me/inter/, licence SIL OFL).
- **JetBrains Mono** — police monospace (logs/code) : `JetBrainsMono-Regular.ttf`
  (https://www.jetbrains.com/lp/mono/, licence SIL OFL).

Le chargeur (`autoflow/ui/theme/fonts.py`) prend automatiquement en compte tout
fichier `.ttf`/`.otf` présent dans ce dossier au démarrage.

**Sans ces fichiers**, l'application retombe proprement sur les piles système
définies dans les tokens (`Segoe UI` / `Consolas`…) — aucune erreur, aucun
téléchargement. Les fichiers ne sont pas versionnés afin de respecter leurs
licences de redistribution ; ajoutez-les lors du packaging si souhaité.
