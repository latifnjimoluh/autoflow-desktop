"""Gestionnaire de déclencheurs : relie les déclencheurs aux workflows.

Indépendant de Qt et **testable** : on lui fournit un rappel ``run_workflow`` qui
démarre un workflow par son nom en recevant l'``TriggerEvent`` (ses variables
sont injectées dans l'exécution). Le démarrage/arrêt « live » est délégué aux
déclencheurs eux-mêmes.
"""

from __future__ import annotations

from collections.abc import Callable

from .base import Trigger, TriggerEvent

RunWorkflow = Callable[[str, TriggerEvent], None]


class TriggerManager:
    """Active/désactive les déclencheurs et route leurs événements."""

    def __init__(self, run_workflow: RunWorkflow) -> None:
        self._run = run_workflow
        # type_name -> liste de (workflow_name, trigger)
        self._bindings: list[tuple[str, Trigger]] = []
        self._active = False

    def clear(self) -> None:
        """Arrête et oublie tous les déclencheurs."""
        self.stop()
        self._bindings = []

    def add(self, workflow_name: str, trigger: Trigger) -> None:
        """Enregistre un déclencheur pour un workflow (démarre si actif)."""
        self._bindings.append((workflow_name, trigger))
        if self._active and trigger.enabled:
            self._start_one(workflow_name, trigger)

    def _start_one(self, workflow_name: str, trigger: Trigger) -> bool:
        return trigger.start(lambda event: self._dispatch(workflow_name, event))

    def _dispatch(self, workflow_name: str, event: TriggerEvent) -> None:
        self._run(workflow_name, event)

    def start(self) -> int:
        """Démarre tous les déclencheurs activés. Renvoie le nombre démarré."""
        self._active = True
        started = 0
        for name, trigger in self._bindings:
            if trigger.enabled and not trigger.is_running():
                if self._start_one(name, trigger):
                    started += 1
        return started

    def stop(self) -> None:
        """Arrête tous les déclencheurs."""
        self._active = False
        for _name, trigger in self._bindings:
            trigger.stop()

    def is_active(self) -> bool:
        return self._active

    def bindings(self) -> list[tuple[str, Trigger]]:
        return list(self._bindings)
