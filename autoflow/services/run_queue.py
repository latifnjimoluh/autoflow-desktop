"""File d'attente / exécution **exclusive** des workflows.

Empêche deux exécutions d'interférer. Deux modes :

- ``exclusive`` : un nouveau démarrage est **refusé** tant qu'une exécution est
  en cours (renvoie ``False``).
- ``queue`` : les démarrages simultanés sont **mis en file** et exécutés l'un
  après l'autre.

Indépendant de Qt et entièrement testable (le « worker » est synchrone par
défaut ; l'UI peut fournir un exécuteur asynchrone).
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from typing import Any


class RunQueue:
    """Coordonne les démarrages de workflows selon une politique d'exclusivité."""

    def __init__(self, mode: str = "queue") -> None:
        self.mode = mode  # "exclusive" | "queue"
        self._lock = threading.RLock()
        self._running: Any = None
        self._pending: deque = deque()

    # -- État --------------------------------------------------------------
    def is_busy(self) -> bool:
        with self._lock:
            return self._running is not None

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    # -- Soumission --------------------------------------------------------
    def submit(self, key: Any, runner: Callable[[], None]) -> bool:
        """Demande l'exécution de ``runner`` (identifié par ``key``).

        Renvoie ``True`` si l'exécution démarre immédiatement, ``False`` si elle
        est refusée (mode exclusif occupé) ou mise en file (mode queue).
        """
        with self._lock:
            if self._running is None:
                self._running = key
                started = True
            elif self.mode == "exclusive":
                return False
            else:  # queue
                self._pending.append((key, runner))
                return False
        if started:
            self._execute(key, runner)
        return True

    def _execute(self, key: Any, runner: Callable[[], None]) -> None:
        try:
            runner()
        finally:
            self.finish(key)

    def finish(self, key: Any) -> None:
        """Signale la fin d'une exécution ; démarre la suivante (mode queue)."""
        with self._lock:
            if self._running == key:
                self._running = None
            if self.mode == "queue" and self._pending and self._running is None:
                next_key, next_runner = self._pending.popleft()
                self._running = next_key
            else:
                return
        # Exécute le suivant hors verrou.
        self._execute(next_key, next_runner)
