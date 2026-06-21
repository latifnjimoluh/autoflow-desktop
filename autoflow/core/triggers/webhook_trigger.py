"""Déclencheur par **webhook** entrant : petit serveur HTTP local (stdlib).

Un serveur ``http.server`` écoute dans un thread ; une requête entrante sur le
chemin configuré démarre le workflow, le **corps JSON** étant exposé en
variables. La logique de traitement (``handle_request``) est pure/testable ; le
serveur n'est démarré qu'en mode live.
"""

from __future__ import annotations

import json
from typing import Any

from .base import ParamSpec, Trigger, TriggerEvent
from .registry import register_trigger


@register_trigger
class WebhookTrigger(Trigger):
    """Démarre un workflow sur réception d'une requête HTTP locale."""

    type_name = "webhook_event"
    label = "Déclencheur : webhook (HTTP local)"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("port", "Port d'écoute", "int", 8765, min_value=1, max_value=65535),
            ParamSpec("path", "Chemin d'URL", "str", "/hook",
                      placeholder="Ex : /hook"),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._server: Any = None
        self._thread: Any = None

    def handle_request(self, path: str, body: str) -> TriggerEvent | None:
        """Traite une requête : vérifie le chemin et expose le corps JSON."""
        expected = str(self.params.get("path", "/hook")) or "/hook"
        # On ignore la query string éventuelle.
        if path.split("?", 1)[0] != expected:
            return None
        variables: dict[str, Any] = {"webhook_body": body}
        try:
            data = json.loads(body) if body else {}
            if isinstance(data, dict):
                for key, value in data.items():
                    variables[f"webhook_{key}"] = value
        except (ValueError, TypeError):
            pass
        return TriggerEvent(
            trigger_type=self.type_name,
            message=f"Webhook reçu sur {expected}",
            variables=variables)

    # -- Live --------------------------------------------------------------
    def _start(self) -> bool:
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        trigger = self

        class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - live
            def log_message(self, *args: Any) -> None:
                pass

            def _process(self) -> None:
                length = int(self.headers.get("Content-Length", 0) or 0)
                body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
                event = trigger.handle_request(self.path, body)
                if event is not None:
                    trigger.fire(event)
                    self.send_response(200)
                else:
                    self.send_response(404)
                self.end_headers()
                self.wfile.write(b"ok" if event is not None else b"ignored")

            def do_POST(self) -> None:  # noqa: N802
                self._process()

            def do_GET(self) -> None:  # noqa: N802
                self._process()

        try:
            port = int(self.params.get("port", 8765))
            self._server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
        except OSError:  # pragma: no cover - port occupé
            return False
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return True

    def _stop(self) -> None:
        if self._server is not None:  # pragma: no cover - live
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def summary(self) -> str:
        return f"Webhook http://127.0.0.1:{self.params.get('port')}{self.params.get('path')}"
