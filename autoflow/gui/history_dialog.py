"""Boîte de dialogue Historique d'exécution et statistiques."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..core.history import HistoryDB


class HistoryDialog(QDialog):
    """Affiche l'historique des exécutions, des stats et un export CSV."""

    _COLS = ["Workflow", "Début", "Fin", "Durée (s)", "Succès", "Itér.", "Erreur"]

    def __init__(self, history: HistoryDB, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Historique — AutoFlow")
        self.resize(720, 460)
        self.history = history
        layout = QVBoxLayout(self)

        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        self.table = QTableWidget(0, len(self._COLS))
        self.table.setHorizontalHeaderLabels(self._COLS)
        layout.addWidget(self.table)

        boutons = QHBoxLayout()
        refresh = QPushButton("Rafraîchir")
        refresh.clicked.connect(self.refresh)
        export = QPushButton("Exporter en CSV")
        export.clicked.connect(self._export_csv)
        boutons.addWidget(refresh)
        boutons.addWidget(export)
        boutons.addStretch(1)
        layout.addLayout(boutons)

        self.refresh()

    def refresh(self) -> None:
        """Recharge la table et les statistiques depuis la base."""
        runs = self.history.list_runs(limit=500)
        self.table.setRowCount(len(runs))
        for row, run in enumerate(runs):
            valeurs = [
                run.get("workflow", ""),
                run.get("started_at", ""),
                run.get("ended_at", ""),
                f"{run.get('duration', 0):.1f}",
                "Oui" if run.get("success") else "Non",
                str(run.get("iterations", 0)),
                run.get("error") or "",
            ]
            for col, val in enumerate(valeurs):
                self.table.setItem(row, col, QTableWidgetItem(str(val)))
        stats = self.history.stats()
        self.stats_label.setText(
            f"Total : {stats['total']}  |  Succès : {stats['reussites']}  |  "
            f"Échecs : {stats['echecs']}  |  Taux : {stats['taux_succes'] * 100:.0f}%  |  "
            f"Durée moy. : {stats['duree_moyenne']:.1f} s  |  "
            f"Dernière : {stats['derniere_execution'] or '—'}")

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter l'historique", "historique_autoflow.csv",
            filter="CSV (*.csv)")
        if path:
            self.history.export_csv(path)
