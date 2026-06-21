"""Service de mise à jour : interroge l'API Releases GitHub (stdlib, mockable).

Aucune dépendance réseau ajoutée : on utilise ``urllib`` de la bibliothèque
standard. L'``opener`` (la fonction qui réalise réellement la requête HTTP) est
**injectable**, de sorte que tous les chemins (succès, erreur réseau, JSON
malformé, Release sans asset, pré-version) sont **testés sans toucher au réseau**.

Comportement défensif : toute anomalie renvoie un :class:`UpdateInfo` neutre
(``available=False``) ou ``None``, jamais une exception qui remonterait jusqu'à
l'UI.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from packaging.version import InvalidVersion, Version

from .version import current_version, github_repo

# Type de l'ouvreur HTTP : (url, timeout) -> texte de la réponse.
Opener = Callable[[str, float], str]

_API_TEMPLATE = "https://api.github.com/repos/{repo}/releases/latest"
_USER_AGENT = "AutoFlow-Updater"
_TIMEOUT = 8.0


@dataclass
class UpdateInfo:
    """Résultat d'une vérification de mise à jour."""

    available: bool = False
    current: str = ""
    latest: str = ""
    notes: str = ""
    asset_url: str = ""          # URL de téléchargement direct de l'asset
    asset_name: str = ""
    html_url: str = ""           # page de la Release (repli de téléchargement)
    error: str = ""              # message si la vérification a échoué

    def download_url(self) -> str:
        """URL à proposer pour télécharger (asset si présent, sinon la Release)."""
        return self.asset_url or self.html_url


def is_update_available(current: str, latest: str) -> bool:
    """Vrai si ``latest`` est une version **stable** strictement supérieure.

    Les pré-versions (``1.2.0rc1``…) sont ignorées (jamais proposées). Toute
    version illisible renvoie ``False`` (on ne propose rien de douteux).
    """
    try:
        cur = Version(current)
        new = Version(latest)
    except InvalidVersion:
        return False
    if new.is_prerelease:
        return False
    return new > cur


def _default_opener(url: str, timeout: float) -> str:
    """Ouvreur HTTP par défaut (stdlib), avec en-têtes GitHub."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8")


def _pick_asset(assets: list[dict]) -> tuple[str, str]:
    """Choisit l'asset téléchargeable (``.exe`` prioritaire, sinon le 1er)."""
    if not assets:
        return "", ""
    for asset in assets:
        name = str(asset.get("name", ""))
        if name.lower().endswith((".exe", ".msi")):
            return str(asset.get("browser_download_url", "")), name
    first = assets[0]
    return str(first.get("browser_download_url", "")), str(first.get("name", ""))


def check_for_updates(
    current: str | None = None,
    repo: str | None = None,
    opener: Opener | None = None,
    timeout: float = _TIMEOUT,
) -> UpdateInfo:
    """Interroge GitHub et renvoie un :class:`UpdateInfo` (jamais d'exception).

    ``opener`` permet d'injecter un faux client HTTP pour les tests.
    """
    current = current or current_version()
    repo = repo or github_repo()
    opener = opener or _default_opener
    info = UpdateInfo(current=current)

    url = _API_TEMPLATE.format(repo=repo)
    try:
        raw = opener(url, timeout)
    except urllib.error.HTTPError as exc:  # rate-limit (403), 404 sans release…
        info.error = f"HTTP {exc.code}"
        return info
    except (urllib.error.URLError, TimeoutError, OSError) as exc:  # réseau absent
        info.error = f"réseau indisponible : {exc.reason if hasattr(exc, 'reason') else exc}"
        return info
    except Exception as exc:  # noqa: BLE001 — garde-fou ultime
        info.error = f"erreur inattendue : {exc}"
        return info

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        info.error = "réponse malformée"
        return info
    if not isinstance(data, dict):
        info.error = "réponse inattendue"
        return info

    tag = str(data.get("tag_name") or data.get("name") or "").lstrip("vV")
    if not tag:
        info.error = "aucune version publiée"
        return info

    info.latest = tag
    info.notes = str(data.get("body") or "").strip()
    info.html_url = str(data.get("html_url") or "")
    assets = data.get("assets")
    if isinstance(assets, list):
        info.asset_url, info.asset_name = _pick_asset(assets)

    info.available = is_update_available(current, tag)
    return info
