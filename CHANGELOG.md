# Changelog

Tous les changements notables d'AutoFlow sont consignés dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet adopte le [versionnement sémantique](https://semver.org/lang/fr/).

## [Non publié]

## [1.0.0] - 2026-06-21

### Ajouté
- **Chaîne de livraison (v5)** : intégration continue GitHub Actions
  (`ci.yml`, tests sur Python 3.11/3.12 en mode offscreen) et **publication
  automatique de Releases** (`release.yml`) — build Windows `.exe` via
  PyInstaller sur `windows-latest`, checksums SHA256 et notes de version.
- **Mise à jour intégrée** : vérification via l'API Releases GitHub (au
  démarrage + bouton « 🔄 Mises à jour »), dialogue de mise à jour
  (Télécharger / Installer), réglage « Vérifier les mises à jour au démarrage ».
- **Versionnement à source unique** (`autoflow.__version__`, lu dynamiquement
  par `pyproject.toml`) et dépôt cible déduit du remote git.
- **Système de design v4** : tokens (source unique de vérité), `ThemeManager`,
  thèmes clair/sombre **basculables à chaud**, icône d'application, fenêtre
  « À propos », toile à nœuds soignée (liserés par catégorie, pastilles d'état).

### Fonctionnalités historiques (v1–v3)
- Cœur d'automatisation (clics, frappes, fenêtres, conditions, boucles,
  variables, vision/OCR), planification avancée, profils, historique SQLite,
  export Python, expérience no-code « façon n8n » (palette, nœuds, assistant),
  configuration concrète des actions et galerie de modèles.

[Non publié]: https://github.com/latifnjimoluh/autoflow-desktop/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/latifnjimoluh/autoflow-desktop/releases/tag/v1.0.0
