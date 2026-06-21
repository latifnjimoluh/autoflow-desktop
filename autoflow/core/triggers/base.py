"""Classe de déclencheur abstraite et description d'événement.

Chaque déclencheur concret décrit ses paramètres via :class:`ParamSpec` (réutilisé
des actions) pour une configuration **concrète/guidée** identique au reste de
l'app. La *logique de détection* est isolée des boucles « live » afin d'être
**testable sans matériel** (on simule l'événement).
"""

from __future__ import annotations

import abc
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..actions.base import ParamSpec

__all__ = ["ParamSpec", "Trigger", "TriggerEvent", "FireCallback"]


@dataclass
class TriggerEvent:
    """Événement émis par un déclencheur, transmis au workflow démarré.

    ``variables`` est injecté dans le magasin de variables du workflow (ex. le
    chemin du fichier détecté, le contenu du presse-papiers, le corps du webhook).
    """

    trigger_type: str = ""
    message: str = ""
    variables: dict[str, Any] = field(default_factory=dict)


# Rappel appelé quand le déclencheur se déclenche.
FireCallback = Callable[[TriggerEvent], None]


class Trigger(abc.ABC):  # noqa: B024 — base extensible (surcharges optionnelles)
    """Déclencheur abstrait : écoute un événement et démarre un workflow."""

    #: Identifiant de type (sérialisation, registre). À surcharger.
    type_name: str = ""
    #: Libellé affiché (français). À surcharger.
    label: str = ""
    #: Catégorie pour le regroupement dans l'interface.
    category: str = "Déclencheurs"

    def __init__(self, params: dict[str, Any] | None = None,
                 enabled: bool = True) -> None:
        self.params: dict[str, Any] = {}
        for spec in self.param_specs():
            self.params[spec.name] = spec.default
        if params:
            self.params.update(params)
        self.enabled = bool(enabled)
        self._on_fire: FireCallback | None = None
        self._running = False

    # -- Schéma ------------------------------------------------------------
    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return []

    # -- Cycle de vie « live » --------------------------------------------
    def start(self, on_fire: FireCallback) -> bool:
        """Démarre l'écoute. Renvoie ``True`` si l'écoute est active.

        Les sous-classes surchargent :meth:`_start`. La logique de *détection*
        reste séparée (testée par simulation), :meth:`_start` ne fait que brancher
        la source d'événements réelle.
        """
        self._on_fire = on_fire
        self._running = self._start()
        return self._running

    def stop(self) -> None:
        """Arrête l'écoute (idempotent)."""
        if self._running:
            self._stop()
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _start(self) -> bool:  # pragma: no cover - surchargé
        return False

    def _stop(self) -> None:  # noqa: B027 — surcharge optionnelle, no-op par défaut
        pass

    # -- Émission ----------------------------------------------------------
    def fire(self, event: TriggerEvent | None = None) -> None:
        """Émet l'événement vers le rappel enregistré (sûr si non démarré)."""
        if self._on_fire is None:
            return
        self._on_fire(event or TriggerEvent(trigger_type=self.type_name))

    # -- Présentation & (dé)sérialisation ---------------------------------
    def summary(self) -> str:
        return self.label or self.type_name

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "params": dict(self.params),
                "enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trigger:
        return cls(params=data.get("params"), enabled=data.get("enabled", True))
