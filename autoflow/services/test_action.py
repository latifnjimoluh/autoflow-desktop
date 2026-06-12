"""Exécuteur « Tester cette action » : lance une seule action isolément.

Permet au bouton *Tester cette action* de l'interface d'exécuter immédiatement
l'action en cours de configuration et de montrer le résultat (ou l'erreur) à
l'utilisateur — pilier de la confiance no-code. Réutilise un contexte minimal
proche de celui du moteur, mais sans planning ni boucle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class TestResult:
    """Résultat d'un test d'action isolée."""

    ok: bool
    value: Any = None
    error: str = ""
    logs: list[str] | None = None

    def message(self) -> str:
        """Renvoie un message lisible pour l'utilisateur."""
        if self.ok:
            return f"Action exécutée avec succès. Résultat : {self.value!r}"
        return f"Échec : {self.error}"


def _build_context(
    inputs: Any,
    windows: Any,
    *,
    variables: Any = None,
    settings: Any = None,
    workflow_resolver: Callable[[str], Any] | None = None,
    logs: list[str] | None = None,
) -> dict[str, Any]:
    """Construit un contexte d'exécution minimal pour une action isolée."""
    from ..core.clipboard import ClipboardBackend
    from ..core.ocr import OcrBackend
    from ..core.variables import VariableStore
    from ..core.vision import VisionBackend

    store = variables if variables is not None else VariableStore()
    sink = logs if logs is not None else []

    def log(message: str, level: str = "info") -> None:
        sink.append(f"[{level}] {message}")

    context: dict[str, Any] = {
        "sleep": lambda _s: None,  # pas d'attente réelle lors d'un test
        "log": log,
        "variables": store,
        "inputs": inputs,
        "windows": windows,
        "settings": settings,
        "iteration": 1,
        "vision": VisionBackend(inputs),
        "ocr": OcrBackend(getattr(settings, "tesseract_path", "") or ""),
        "clipboard": ClipboardBackend(),
        "workflow_resolver": workflow_resolver,
        "call_stack": [],
    }
    # Les actions de contrôle exécutent leurs enfants via ce rappel.
    context["run_actions"] = lambda actions: [
        a.execute(inputs, windows, context) for a in actions if getattr(a, "enabled", True)
    ]
    return context


def test_action(
    action: Any,
    inputs: Any,
    windows: Any,
    *,
    variables: Any = None,
    settings: Any = None,
    workflow_resolver: Callable[[str], Any] | None = None,
) -> TestResult:
    """Exécute ``action`` une seule fois et renvoie un :class:`TestResult`.

    Aucune exception n'est propagée : toute erreur est capturée et reportée dans
    le résultat, afin que l'appelant (l'interface) puisse l'afficher sereinement.
    """
    logs: list[str] = []
    context = _build_context(
        inputs, windows,
        variables=variables, settings=settings,
        workflow_resolver=workflow_resolver, logs=logs,
    )
    try:
        # Valide d'abord si l'action le permet (messages d'erreur concrets).
        validate = getattr(action, "validate", None)
        if callable(validate):
            validate()
        value = action.execute(inputs, windows, context)
        return TestResult(ok=True, value=value, logs=logs)
    except Exception as exc:  # noqa: BLE001 - on rapporte, on ne propage pas
        return TestResult(ok=False, error=str(exc) or type(exc).__name__, logs=logs)
