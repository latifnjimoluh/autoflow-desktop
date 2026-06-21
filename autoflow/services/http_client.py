"""Client HTTP minimal basé sur la **bibliothèque standard** (`urllib`).

Aucune dépendance réseau ajoutée. L'``opener`` (fonction qui réalise vraiment la
requête) est **injectable**, ce qui rend l'action HTTP entièrement testable sans
toucher au réseau.
"""

from __future__ import annotations

import json as _json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# (method, url, headers, body_bytes, timeout) -> (status, text, response_headers)
Opener = Callable[[str, str, dict, bytes | None, float], tuple]

_TIMEOUT = 15.0


@dataclass
class HttpResponse:
    """Réponse HTTP normalisée."""

    status: int = 0
    text: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""

    def json(self) -> Any:
        """Tente de décoder le corps en JSON (``None`` si impossible)."""
        try:
            return _json.loads(self.text)
        except (ValueError, TypeError):
            return None


def _default_opener(method: str, url: str, headers: dict,
                    body: bytes | None, timeout: float) -> tuple:
    request = urllib.request.Request(url, data=body, method=method.upper())
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        raw = response.read().decode("utf-8", errors="replace")
        return response.status, raw, dict(response.headers)


def request(method: str, url: str, headers: dict | None = None,
            body: str | bytes | None = None, timeout: float = _TIMEOUT,
            opener: Opener | None = None) -> HttpResponse:
    """Effectue une requête HTTP et renvoie un :class:`HttpResponse` (jamais d'exception)."""
    opener = opener or _default_opener
    payload: bytes | None
    if isinstance(body, str):
        payload = body.encode("utf-8") if body else None
    else:
        payload = body
    try:
        status, text, resp_headers = opener(method, url, headers or {}, payload, timeout)
        return HttpResponse(status=int(status), text=str(text),
                            headers=dict(resp_headers or {}))
    except urllib.error.HTTPError as exc:  # 4xx/5xx renvoyés proprement
        body_text = ""
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
        return HttpResponse(status=int(exc.code), text=body_text, error=f"HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HttpResponse(error=f"réseau : {getattr(exc, 'reason', exc)}")
    except Exception as exc:  # noqa: BLE001
        return HttpResponse(error=f"erreur : {exc}")
