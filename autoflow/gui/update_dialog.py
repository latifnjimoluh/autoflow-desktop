"""Vérification de mise à jour côté UI : thread non bloquant + dialogue soigné.

- :class:`UpdateChecker` exécute :func:`autoflow.services.updater.check_for_updates`
  dans un ``QThread`` et émet le résultat (jamais d'exception fatale).
- :class:`UpdateDialog` présente la nouvelle version et ses notes, avec les
  actions **Télécharger** (ouvre l'asset/Release) et **Installer** (télécharge
  puis lance et quitte l'app — un ``.exe`` en cours d'exécution ne peut être
  écrasé). Construit proprement en mode offscreen (testé).
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from ..services.updater import UpdateInfo, check_for_updates


class UpdateChecker(QThread):
    """Thread de vérification de mise à jour (n'interrompt jamais l'UI)."""

    finished_check = Signal(object)  # émet un UpdateInfo

    def __init__(self, current: str | None = None, repo: str | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._current = current
        self._repo = repo

    def run(self) -> None:  # pragma: no cover - exécuté dans un thread Qt
        try:
            info = check_for_updates(current=self._current, repo=self._repo)
        except Exception as exc:  # noqa: BLE001 — garde-fou
            info = UpdateInfo(error=str(exc))
        self.finished_check.emit(info)


class UpdateDialog(QDialog):
    """Dialogue proposant une mise à jour (télécharger / installer)."""

    def __init__(self, info: UpdateInfo, parent=None) -> None:
        super().__init__(parent)
        self.info = info
        self._do_install = False
        self.setWindowTitle("Mise à jour disponible — AutoFlow")
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)

        title = QLabel(f"AutoFlow {info.latest} est disponible")
        title.setProperty("variant", "title")
        root.addWidget(title)

        sub = QLabel(f"Version installée : {info.current}")
        sub.setProperty("variant", "muted")
        root.addWidget(sub)

        if info.notes:
            notes = QPlainTextEdit(info.notes)
            notes.setReadOnly(True)
            notes.setMinimumHeight(160)
            root.addWidget(notes)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        later = QPushButton("Plus tard")
        later.setProperty("variant", "ghost")
        later.clicked.connect(self.reject)
        buttons.addWidget(later)

        download = QPushButton("Télécharger")
        download.clicked.connect(self._download)
        buttons.addWidget(download)

        install = QPushButton("Installer et redémarrer")
        install.setProperty("variant", "primary")
        install.clicked.connect(self._install)
        if not info.asset_url:
            install.setEnabled(False)
            install.setToolTip("Aucun fichier d'installation dans cette Release.")
        buttons.addWidget(install)
        root.addLayout(buttons)

    # -- Actions -----------------------------------------------------------
    def _download(self) -> None:
        """Ouvre l'URL de téléchargement (asset si présent, sinon la Release)."""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        url = self.info.download_url()
        if url:
            QDesktopServices.openUrl(QUrl(url))
        self.accept()

    def _install(self) -> None:
        """Marque l'intention d'installer ; le téléchargement réel est délégué."""
        self._do_install = True
        self.accept()

    @property
    def wants_install(self) -> bool:
        """Vrai si l'utilisateur a choisi « Installer »."""
        return self._do_install
