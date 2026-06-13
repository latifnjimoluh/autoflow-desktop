"""Pont entre le moteur d'exécution et l'interface (signaux Qt thread-safe)."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from ..core.executor import Executor
from ..models.workflow import Workflow


class ExecutorWorker(QObject):
    """Exécute un workflow dans un thread et relaie l'avancement en signaux Qt.

    Les rappels du moteur (appelés depuis le thread de travail) émettent des
    signaux Qt ; la connexion en file d'attente garantit que l'interface est
    mise à jour dans le thread principal, sans jamais geler.
    """

    log = Signal(str, str)
    status = Signal(str)
    iteration = Signal(int)
    finished = Signal(int)

    def __init__(self, workflow: Workflow, inputs, windows,
                 continue_on_error: bool = True) -> None:
        super().__init__()
        self.executor = Executor(
            workflow,
            inputs,
            windows,
            log=self.log.emit,
            on_status=self.status.emit,
            on_iteration=self.iteration.emit,
            continue_on_error=continue_on_error,
        )

    @Slot()
    def run(self) -> None:
        """Lance l'exécution (à connecter à ``QThread.started``)."""
        count = self.executor.run()
        self.finished.emit(count)

    # -- Commandes (sûres depuis le thread interface) ---------------------
    def pause(self) -> None:
        self.executor.pause()

    def resume(self) -> None:
        self.executor.resume()

    def request_stop(self) -> None:
        self.executor.request_stop()

    def is_paused(self) -> bool:
        return self.executor.is_paused()
