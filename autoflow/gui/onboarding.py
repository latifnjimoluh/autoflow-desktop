"""Accueil au premier lancement + assistant de création de workflow.

- :class:`WelcomeDialog` : écran d'accueil affiché au tout premier démarrage, qui
  oriente l'utilisateur (partir d'un modèle, créer de zéro, ou découvrir).
- :class:`CreationWizard` : assistant pas-à-pas qui guide la construction d'un
  premier workflow (nom, première action, planification) en langage simple.

Les deux retournent un *résultat* lisible par la fenêtre principale, sans la
coupler à la logique d'interface.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from ..core import registry
from ..models.workflow import Schedule, Workflow


class WelcomeDialog(QDialog):
    """Écran d'accueil du premier lancement (choix d'un point de départ)."""

    # Choix possibles renvoyés via :attr:`choice`.
    GALLERY = "gallery"
    WIZARD = "wizard"
    SCRATCH = "scratch"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bienvenue dans AutoFlow")
        self.resize(520, 360)
        self.choice: str | None = None

        layout = QVBoxLayout(self)
        title = QLabel("<h2>👋 Bienvenue dans AutoFlow</h2>")
        layout.addWidget(title)
        intro = QLabel(
            "AutoFlow automatise votre PC <b>sans écrire de code</b> : assemblez "
            "des actions (clics, frappes, fenêtres…) et planifiez-les.<br><br>"
            "Comment souhaitez-vous commencer ?")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        from PySide6.QtWidgets import QPushButton

        btn_gallery = QPushButton("📚  Partir d'un modèle prêt à l'emploi")
        btn_gallery.clicked.connect(lambda: self._pick(self.GALLERY))
        btn_wizard = QPushButton("🧭  Être guidé pas à pas (assistant)")
        btn_wizard.clicked.connect(lambda: self._pick(self.WIZARD))
        btn_scratch = QPushButton("✏  Créer un workflow vide")
        btn_scratch.clicked.connect(lambda: self._pick(self.SCRATCH))
        for btn in (btn_gallery, btn_wizard, btn_scratch):
            btn.setMinimumHeight(44)
            layout.addWidget(btn)
        layout.addStretch(1)

    def _pick(self, choice: str) -> None:
        self.choice = choice
        self.accept()


class CreationWizard(QWizard):
    """Assistant guidé : nom → première action → planification."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Assistant de création d'un workflow")
        self.resize(560, 420)

        # Page 1 : nom & description.
        page_name = QWizardPage()
        page_name.setTitle("1. Nommez votre workflow")
        form1 = QFormLayout(page_name)
        self.name_edit = QLineEdit("Mon premier workflow")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Ex : garder mon PC éveillé")
        form1.addRow("Nom", self.name_edit)
        form1.addRow("Description (optionnel)", self.desc_edit)
        self.addPage(page_name)

        # Page 2 : première action.
        page_action = QWizardPage()
        page_action.setTitle("2. Choisissez une première action")
        form2 = QFormLayout(page_action)
        self.action_combo = QComboBox()
        for type_name, label in registry.available_types():
            self.action_combo.addItem(label, type_name)
        hint = QLabel("Vous pourrez en ajouter d'autres ensuite.")
        hint.setWordWrap(True)
        form2.addRow("Action", self.action_combo)
        form2.addRow(hint)
        self.addPage(page_action)

        # Page 3 : planification.
        page_sched = QWizardPage()
        page_sched.setTitle("3. Quand l'exécuter ?")
        form3 = QFormLayout(page_sched)
        self.sched_combo = QComboBox()
        self._sched_modes = [
            ("run_once", "Une seule fois"),
            ("loop_interval", "En boucle (toutes les X secondes)"),
            ("at_time", "À une heure précise"),
            ("hotkey_trigger", "Quand j'appuie sur un raccourci"),
        ]
        for mode, label in self._sched_modes:
            self.sched_combo.addItem(label, mode)
        form3.addRow("Déclenchement", self.sched_combo)
        self.addPage(page_sched)

    def build_workflow(self) -> Workflow:
        """Construit le workflow décrit par l'assistant."""
        mode = self.sched_combo.currentData() or "run_once"
        wf = Workflow(
            name=self.name_edit.text().strip() or "Nouveau workflow",
            description=self.desc_edit.text().strip(),
            schedule=Schedule(mode=mode),
        )
        type_name = self.action_combo.currentData()
        if type_name:
            wf.actions.append(registry.create_action(type_name))
        return wf
