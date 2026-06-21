"""Action HTTP / API : requête GET/POST/PUT/DELETE avec capture de la réponse."""

from __future__ import annotations

import json
from typing import Any

from ...services import http_client
from ..registry import register
from .base import Action, ParamSpec


@register
class HttpRequestAction(Action):
    """Appelle une URL et stocke statut + corps (et un champ JSON) en variables."""

    type_name = "http_request"
    label = "Requête HTTP / API"
    category = "Données"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("method", "Méthode", "choice", "GET",
                      choices=["GET", "POST", "PUT", "DELETE", "PATCH"]),
            ParamSpec("url", "URL", "str", "", supports_vars=True,
                      placeholder="Ex : https://api.exemple.com/v1/etat"),
            ParamSpec("headers", "En-têtes (JSON)", "text", "",
                      supports_vars=True,
                      placeholder='Ex : {"Authorization": "Bearer {{cle}}"}'),
            ParamSpec("body", "Corps de la requête", "text", "", supports_vars=True,
                      depends_on=("method", ("POST", "PUT", "PATCH", "DELETE")),
                      placeholder='Ex : {"nom": "{{nom}}"}'),
            ParamSpec("json_body", "Envoyer en JSON", "bool", True,
                      depends_on=("method", ("POST", "PUT", "PATCH", "DELETE"))),
            ParamSpec("timeout", "Délai maximum (s)", "float", 15.0, min_value=0.1),
            ParamSpec("response_var", "Stocker la réponse dans la variable",
                      "variable", "reponse"),
            ParamSpec("json_path", "Extraire ce champ JSON (optionnel)", "str", "",
                      placeholder="Ex : data.0.id"),
        ]

    def validate(self) -> None:
        if not str(self.params.get("url", "")).strip():
            raise ValueError("L'URL ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        method = str(self.params.get("method", "GET")).upper()
        url = str(self._resolve(self.params.get("url", ""), context))
        headers = self._parse_headers(context)
        body = self._resolve(self.params.get("body", ""), context) or None
        if body and bool(self.params.get("json_body", True)):
            headers.setdefault("Content-Type", "application/json")
        opener = (context or {}).get("http_opener")  # injection pour tests
        resp = http_client.request(
            method, url, headers=headers, body=body,
            timeout=float(self.params.get("timeout", 15.0) or 15.0),
            opener=opener)
        self._store(resp, context)
        log = (context or {}).get("log")
        if callable(log):
            if resp.error:
                log(f"HTTP {method} {url} échec : {resp.error}", "warning")
            else:
                log(f"HTTP {method} {url} → {resp.status}", "info")
        return resp.status

    def _parse_headers(self, context: dict[str, Any]) -> dict[str, str]:
        raw = str(self._resolve(self.params.get("headers", ""), context)).strip()
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return {str(k): str(v) for k, v in data.items()}
        except (ValueError, AttributeError):
            return {}

    def _store(self, resp: http_client.HttpResponse, context: dict[str, Any]) -> None:
        store = (context or {}).get("variables")
        var = str(self.params.get("response_var", "")).strip()
        if store is None or not var:
            return
        store.set(var, resp.text)
        store.set(f"{var}_status", resp.status)
        path = str(self.params.get("json_path", "")).strip()
        if path:
            store.set(f"{var}_value", _dig(resp.json(), path))

    def summary(self) -> str:
        return f"{self.params.get('method')} {self.params.get('url')}"


def _dig(data: Any, path: str) -> Any:
    """Extrait un champ imbriqué via un chemin pointé (``a.b.0.c``)."""
    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current
