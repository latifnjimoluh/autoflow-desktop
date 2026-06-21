"""Actions système : volume, verrouillage, veille, arrêt/redémarrage.

Les actions destructrices (arrêt/redémarrage) exigent une **confirmation
explicite** (paramètre ``confirm``) avant d'agir. Sous un OS non Windows, ces
actions **dégradent proprement** (message clair, pas de crash).
"""

from __future__ import annotations

from typing import Any

from ...services import system_control
from ..registry import register
from .base import Action, ParamSpec

POWER_ACTIONS = {
    "lock": "Verrouiller la session",
    "sleep": "Mettre en veille",
    "shutdown": "Éteindre l'ordinateur",
    "restart": "Redémarrer l'ordinateur",
}


@register
class PowerAction(Action):
    """Verrouille / met en veille / éteint / redémarre (avec confirmation)."""

    type_name = "system_power"
    label = "Alimentation & session"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("action", "Action", "choice", "lock",
                      choices=list(POWER_ACTIONS.keys())),
            ParamSpec("delay", "Délai avant arrêt (s)", "int", 5, min_value=0,
                      depends_on=("action", ("shutdown", "restart"))),
            ParamSpec("confirm", "Je confirme cette action", "bool", False,
                      depends_on=("action", ("shutdown", "restart")),
                      help="Obligatoire pour éteindre ou redémarrer."),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        action = str(self.params.get("action", "lock"))
        runner = (context or {}).get("system_runner")  # injection pour tests
        log = (context or {}).get("log")
        if action in ("shutdown", "restart") and not bool(self.params.get("confirm")):
            if callable(log):
                log("Arrêt/redémarrage non confirmé : action ignorée.", "warning")
            return False
        ok = self._dispatch(action, runner)
        if not ok and callable(log):
            log(f"« {POWER_ACTIONS.get(action, action)} » indisponible sur ce système.",
                "warning")
        return ok

    def _dispatch(self, action: str, runner) -> bool:
        delay = int(self.params.get("delay", 5) or 0)
        if action == "lock":
            return system_control.lock_session(runner=runner)
        if action == "sleep":
            return system_control.sleep_machine(runner=runner)
        if action == "shutdown":
            return system_control.shutdown(restart=False, delay=delay, runner=runner)
        if action == "restart":
            return system_control.shutdown(restart=True, delay=delay, runner=runner)
        raise ValueError(f"Action d'alimentation inconnue : {action!r}")

    def summary(self) -> str:
        return POWER_ACTIONS.get(str(self.params.get("action")), "Alimentation")


@register
class VolumeAction(Action):
    """Règle ou coupe le volume principal du système."""

    type_name = "set_volume"
    label = "Régler le volume"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("mute", "Couper le son", "bool", False),
            ParamSpec("level", "Niveau (0–100)", "int", 50, min_value=0, max_value=100,
                      depends_on=("mute", False)),
        ]

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        controller = (context or {}).get("volume_controller")  # injection test
        if bool(self.params.get("mute")):
            return system_control.mute(controller=controller)
        return system_control.set_volume(int(self.params.get("level", 50)),
                                         controller=controller)

    def summary(self) -> str:
        if self.params.get("mute"):
            return "Couper le son"
        return f"Volume = {self.params.get('level')} %"
