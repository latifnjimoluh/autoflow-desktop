"""Tableau de bord d'accueil : vue d'ensemble des workflows et de l'activité.

S'appuie sur l'historique SQLite existant (taux de succès, exécutions récentes)
et sur la liste des workflows (planifiés / réactifs, prochaines exécutions). Les
données sont fournies par des *providers* injectés, ce qui rend le widget
**construisible et testable** sans le reste de l'application.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..ui.theme import apply_elevation


def _stat_card(title: str, value: str, badge: str = "") -> QFrame:
    """Construit une petite carte de statistique (titre + valeur)."""
    card = QFrame()
    card.setProperty("variant", "card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 12, 16, 12)
    caption = QLabel(title)
    caption.setProperty("variant", "muted")
    val = QLabel(value)
    val.setProperty("variant", "display")
    if badge:
        val.setProperty("badge", badge)
    layout.addWidget(caption)
    layout.addWidget(val)
    apply_elevation(card, 1)
    return card


class DashboardWidget(QWidget):
    """Vue synthétique : statistiques, prochaines exécutions, activité récente."""

    run_requested = Signal(str)
    stop_requested = Signal()

    def __init__(self, history: Any = None,
                 workflows_provider: Callable[[], list[Any]] | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._history = history
        self._workflows_provider = workflows_provider or (lambda: [])
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Tableau de bord")
        title.setProperty("variant", "title")
        root.addWidget(title)

        self._cards = QGridLayout()
        self._cards.setSpacing(12)
        root.addLayout(self._cards)

        actions = QHBoxLayout()
        self._btn_run = QPushButton("▶ Démarrer le workflow sélectionné")
        self._btn_run.setProperty("variant", "primary")
        self._btn_run.clicked.connect(self._emit_run)
        self._btn_stop = QPushButton("⏹ Tout arrêter")
        self._btn_stop.clicked.connect(self.stop_requested.emit)
        actions.addWidget(self._btn_run)
        actions.addWidget(self._btn_stop)
        actions.addStretch(1)
        root.addLayout(actions)

        recent_label = QLabel("Exécutions récentes")
        recent_label.setProperty("variant", "subtitle")
        root.addWidget(recent_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Workflow", "Début", "Durée", "Résultat"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table, 1)

        self._next_label = QLabel("")
        self._next_label.setProperty("variant", "muted")
        self._next_label.setWordWrap(True)
        root.addWidget(self._next_label)

    # -- Données -----------------------------------------------------------
    def refresh(self) -> None:
        """Recharge les statistiques et l'activité depuis les sources."""
        workflows = list(self._workflows_provider())
        stats = self._history.stats() if self._history is not None else {}
        self._render_cards(workflows, stats)
        self._render_recent()
        self._render_next(workflows)

    def _render_cards(self, workflows: list[Any], stats: dict) -> None:
        while self._cards.count():
            item = self._cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        scheduled = sum(1 for w in workflows
                        if getattr(getattr(w, "schedule", None), "mode", "run_once")
                        != "run_once")
        reactive = sum(1 for w in workflows if getattr(w, "triggers", []))
        taux = stats.get("taux_succes", 0.0) * 100
        badge = "success" if taux >= 80 else ("warning" if taux >= 50 else "error")
        cards = [
            _stat_card("Workflows", str(len(workflows))),
            _stat_card("Planifiés", str(scheduled)),
            _stat_card("Réactifs (déclencheurs)", str(reactive)),
            _stat_card("Taux de succès", f"{taux:.0f} %", badge if stats.get("total") else ""),
        ]
        for i, card in enumerate(cards):
            self._cards.addWidget(card, 0, i)

    def _render_recent(self) -> None:
        runs = self._history.list_runs(limit=12) if self._history is not None else []
        self.table.setRowCount(len(runs))
        for row, run in enumerate(runs):
            ok = "✔ Succès" if run.get("success") else "✖ Échec"
            values = [str(run.get("workflow", "")), str(run.get("started_at", "")),
                      f"{run.get('duration', 0):.1f} s", ok]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _render_next(self, workflows: list[Any]) -> None:
        planned = [getattr(w, "name", "?") for w in workflows
                   if getattr(getattr(w, "schedule", None), "mode", "run_once")
                   in ("at_time", "loop_interval", "cron")]
        if planned:
            self._next_label.setText("Prochaines exécutions planifiées : "
                                     + ", ".join(planned[:8]))
        else:
            self._next_label.setText("Aucune exécution planifiée.")

    def selected_workflow(self) -> str:
        item = self.table.item(self.table.currentRow(), 0)
        return item.text() if item is not None else ""

    def _emit_run(self) -> None:
        name = self.selected_workflow()
        if name:
            self.run_requested.emit(name)
