"""Envoi d'e-mails via SMTP (bibliothèque standard ``smtplib``).

Le *transport* est **injectable** (``sender``) pour les tests : aucun test ne
contacte un vrai serveur SMTP. La construction du message (avec pièce jointe)
est pure et testable séparément.
"""

from __future__ import annotations

import smtplib
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path


@dataclass
class SmtpConfig:
    """Paramètres de connexion SMTP."""

    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    sender: str = ""


def build_message(config: SmtpConfig, to: str, subject: str, body: str,
                  attachment: str | None = None) -> EmailMessage:
    """Construit le message e-mail (avec pièce jointe optionnelle)."""
    msg = EmailMessage()
    msg["From"] = config.sender or config.username
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment:
        path = Path(attachment)
        if path.exists():
            data = path.read_bytes()
            msg.add_attachment(data, maintype="application", subtype="octet-stream",
                               filename=path.name)
    return msg


# Type du transport : (config, message) -> None
Sender = Callable[[SmtpConfig, EmailMessage], None]


def _default_sender(config: SmtpConfig, message: EmailMessage) -> None:
    with smtplib.SMTP(config.host, config.port, timeout=20) as server:
        if config.use_tls:
            server.starttls()
        if config.username:
            server.login(config.username, config.password)
        server.send_message(message)


def send_email(config: SmtpConfig, to: str, subject: str, body: str,
               attachment: str | None = None, sender: Sender | None = None) -> None:
    """Envoie un e-mail. ``sender`` injectable pour les tests."""
    message = build_message(config, to, subject, body, attachment)
    (sender or _default_sender)(config, message)
