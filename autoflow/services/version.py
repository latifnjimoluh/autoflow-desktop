"""Versionnement : source unique de vérité + dépôt GitHub cible.

- :func:`current_version` lit ``autoflow.__version__`` (l'unique source).
- :func:`github_repo` déduit ``OWNER/REPO`` du **remote git réel**
  (``git remote get-url origin``), avec un repli sur la constante connue.

Tout est **pur et testable** : ``github_repo`` accepte une URL en argument, de
sorte qu'aucun test n'a besoin d'un vrai dépôt git.
"""

from __future__ import annotations

import re
import subprocess

from .. import __version__

# Repli si le remote est indisponible (clone sans origine, archive…).
DEFAULT_REPO = "latifnjimoluh/autoflow-desktop"

_GITHUB_RE = re.compile(
    r"github\.com[:/]+(?P<owner>[^/]+?)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def current_version() -> str:
    """Renvoie la version courante de l'application (SemVer)."""
    return __version__


def parse_repo(url: str | None) -> str | None:
    """Extrait ``OWNER/REPO`` d'une URL de remote GitHub (HTTPS ou SSH).

    Renvoie ``None`` si l'URL n'est pas une URL GitHub reconnaissable.
    """
    if not url:
        return None
    match = _GITHUB_RE.search(url.strip())
    if not match:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"


def _remote_url() -> str | None:
    """Renvoie l'URL du remote ``origin`` (ou ``None`` en cas d'échec)."""
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def github_repo(url: str | None = None) -> str:
    """Renvoie le dépôt cible ``OWNER/REPO``.

    Si ``url`` est fourni, on le parse directement (utile en test). Sinon on
    interroge le remote git ; en dernier recours, on renvoie :data:`DEFAULT_REPO`.
    """
    if url is None:
        url = _remote_url()
    return parse_repo(url) or DEFAULT_REPO
