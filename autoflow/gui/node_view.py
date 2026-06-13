"""Vue en nœuds « façon n8n » : flux vertical structuré et lisible.

Représente le workflow comme un **enchaînement de cartes** (icône, titre, résumé
en langage naturel, état activé/désactivé) reliées par des connecteurs, avec un
bouton **« + »** entre chaque étape pour insérer une action. Les conditions
affichent leurs branches *Alors / Sinon* et les boucles leur *corps*. La vue
supporte le **pan** (glisser) et le **zoom** (molette).

Elle conserve le **modèle de données structuré existant** : c'est une projection
visuelle de ``workflow.actions``, pas un graphe libre.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..core.actions.base import Action
from .icons import action_icon
from .theme import palette

_CARD_WIDTH = 340
_X = 40
_GAP = 26
_PALETTE = palette("dark")


def _safe_summary(action: Action) -> str:
    """Renvoie le résumé en langage naturel d'une action (repli robuste)."""
    try:
        return action.summary()
    except Exception:  # noqa: BLE001
        return action.type_name


class _NodeCard(QFrame):
    """Carte visuelle représentant une action (icône, titre, résumé, état)."""

    def __init__(self, index: int, action: Action, on_edit, on_select) -> None:
        super().__init__()
        self.setObjectName("nodeCard")
        self.setFixedWidth(_CARD_WIDTH)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        enabled = getattr(action, "enabled", True)
        p = _PALETTE
        border = p["accent"] if enabled else p["border"]
        bg = p["surface"] if enabled else p["surface_alt"]
        self.setStyleSheet(
            f"#nodeCard {{ border: 1px solid {border}; border-left: 4px solid {border}; "
            f"border-radius: 10px; background: {bg}; }}"
            f"#nodeCard:hover {{ border-color: {p['accent_hover']}; "
            f"border-left-color: {p['accent_hover']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        header = QHBoxLayout()
        icon = action_icon(action.type_name, getattr(action, "category", "Général"))
        title = QLabel(f"{icon}  <b>{action.label or action.type_name}</b>")
        title.setTextFormat(Qt.TextFormat.RichText)
        header.addWidget(title, 1)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {p['success'] if enabled else p['muted']};")
        dot.setToolTip("Activée" if enabled else "Désactivée")
        header.addWidget(dot)
        layout.addLayout(header)

        summary = QLabel(_safe_summary(action))
        summary.setWordWrap(True)
        summary.setStyleSheet(f"color: {p['muted']};")
        layout.addWidget(summary)

        # Branches / corps pour les conteneurs (condition, boucle).
        groups = action.child_groups()
        if groups:
            desc = " · ".join(f"{name.capitalize()} : {len(acts)}"
                              for name, acts in groups.items())
            branch = QLabel("↳ " + desc)
            branch.setStyleSheet(f"color: {_PALETTE['accent']};")
            layout.addWidget(branch)

        edit_btn = QPushButton("⚙ Configurer")
        edit_btn.clicked.connect(lambda: on_edit(index))
        layout.addWidget(edit_btn)

        self._on_select = on_select
        self._index = index

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._on_select(self._index)
        super().mousePressEvent(event)


class NodeView(QGraphicsView):
    """Projection visuelle en flux vertical des actions d'un workflow."""

    action_selected = Signal(int)
    edit_requested = Signal(int)
    insert_requested = Signal(int)  # position d'insertion

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor(_PALETTE["window"]))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self._zoom = 1.0
        self._actions: list[Action] = []

    # -- Rendu -------------------------------------------------------------
    def set_actions(self, actions: list[Action], current: int = -1) -> None:
        """Reconstruit la vue à partir de la liste d'actions."""
        self._actions = actions
        self._scene.clear()
        y = 20

        # Carte de départ (point d'entrée du flux).
        start = QLabel("  ▶  Début du workflow")
        start.setStyleSheet(f"color: {_PALETTE['success']}; font-weight: bold;")
        self._scene.addWidget(start).setPos(_X, y)
        y += 32

        y = self._add_plus(0, y)

        for i, action in enumerate(actions):
            card = _NodeCard(i, action, self.edit_requested.emit,
                             self.action_selected.emit)
            proxy = self._scene.addWidget(card)
            proxy.setPos(_X, y)
            y += card.sizeHint().height() + 8
            self._draw_connector(y)
            y = self._add_plus(i + 1, y)

        end = QLabel("  ⛔  Fin du workflow")
        end.setStyleSheet(f"color: {_PALETTE['danger']}; font-weight: bold;")
        self._scene.addWidget(end).setPos(_X, y)
        y += 40

        self._scene.setSceneRect(0, 0, _CARD_WIDTH + 2 * _X, max(y, 200))

    def _add_plus(self, position: int, y: int) -> int:
        """Ajoute un bouton « + » d'insertion à la position donnée."""
        holder = QWidget()
        box = QHBoxLayout(holder)
        box.setContentsMargins(0, 0, 0, 0)
        btn = QToolButton()
        btn.setText("➕")
        btn.setToolTip("Insérer une action ici")
        btn.clicked.connect(lambda: self.insert_requested.emit(position))
        box.addWidget(btn)
        box.addStretch(1)
        proxy = self._scene.addWidget(holder)
        proxy.setPos(_X + _CARD_WIDTH / 2 - 16, y)
        return y + _GAP

    def _draw_connector(self, y: int) -> None:
        """Trace un petit connecteur vertical entre deux étapes."""
        pen = QPen(QColor(_PALETTE["border_strong"]))
        pen.setWidth(2)
        self._scene.addLine(_X + _CARD_WIDTH / 2, y - 8,
                            _X + _CARD_WIDTH / 2, y + 2, pen)

    # -- Pan / zoom --------------------------------------------------------
    def wheelEvent(self, event) -> None:  # noqa: N802
        """Zoom à la molette (Ctrl non requis pour rester simple)."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = self._zoom * factor
        if 0.4 <= new_zoom <= 2.5:
            self._zoom = new_zoom
            self.scale(factor, factor)
