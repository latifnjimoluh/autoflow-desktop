"""Déclencheur par fichier/dossier (surveillance via ``watchdog``).

La logique de filtrage (motif/extension, type d'événement) est **pure et
testée** via :meth:`handle_event`. ``watchdog`` est importé **paresseusement**
pour la surveillance live et n'est pas requis par les tests.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from .base import ParamSpec, Trigger, TriggerEvent
from .registry import register_trigger

FILE_EVENTS = {
    "created": "Fichier ajouté",
    "modified": "Fichier modifié",
    "deleted": "Fichier supprimé",
    "any": "Tout changement",
}


@register_trigger
class FileTrigger(Trigger):
    """Démarre un workflow quand un fichier d'un dossier change."""

    type_name = "file_event"
    label = "Déclencheur : fichier / dossier"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("folder", "Dossier à surveiller", "folder", "",
                      placeholder="Ex : C:\\Téléchargements"),
            ParamSpec("event", "Événement", "choice", "created",
                      choices=list(FILE_EVENTS.keys())),
            ParamSpec("pattern", "Filtre (motif)", "str", "*",
                      placeholder="Ex : *.pdf"),
            ParamSpec("recursive", "Inclure les sous-dossiers", "bool", False),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._observer: Any = None

    def handle_event(self, event_type: str, path: str) -> TriggerEvent | None:
        """Filtre un événement de fichier et renvoie un :class:`TriggerEvent` ou ``None``."""
        wanted = str(self.params.get("event", "created"))
        if wanted != "any" and event_type != wanted:
            return None
        pattern = str(self.params.get("pattern", "*") or "*")
        name = Path(str(path)).name
        if not fnmatch.fnmatch(name, pattern):
            return None
        return TriggerEvent(
            trigger_type=self.type_name,
            message=f"{FILE_EVENTS.get(event_type, event_type)} : {path}",
            variables={"file_path": str(path), "file_name": name,
                       "file_event": event_type})

    # -- Live (watchdog) ---------------------------------------------------
    def _start(self) -> bool:
        folder = str(self.params.get("folder", "")).strip()
        if not folder or not Path(folder).is_dir():
            return False
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:  # pragma: no cover - dépend de l'environnement
            return False

        trigger = self

        class _Handler(FileSystemEventHandler):  # pragma: no cover - live
            def on_any_event(self, event: Any) -> None:
                if event.is_directory:
                    return
                mapping = {"created": "created", "modified": "modified",
                           "deleted": "deleted"}
                etype = mapping.get(event.event_type)
                if etype is None:
                    return
                fired = trigger.handle_event(etype, event.src_path)
                if fired is not None:
                    trigger.fire(fired)

        self._observer = Observer()
        self._observer.schedule(
            _Handler(), folder, recursive=bool(self.params.get("recursive", False)))
        self._observer.start()
        return True

    def _stop(self) -> None:
        if self._observer is not None:  # pragma: no cover - live
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None

    def summary(self) -> str:
        return (f"{FILE_EVENTS.get(self.params.get('event'), 'Changement')} "
                f"dans « {self.params.get('folder')} » ({self.params.get('pattern')})")
