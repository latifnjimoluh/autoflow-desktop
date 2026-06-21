"""Action e-mail : envoie un message SMTP (destinataire, sujet, corps, PJ).

Les identifiants SMTP proviennent des **réglages** et du **coffre de secrets**
(le mot de passe n'est jamais stocké en clair dans le workflow).
"""

from __future__ import annotations

from typing import Any

from ...services import email_smtp
from ..registry import register
from .base import Action, ParamSpec


@register
class SendEmailAction(Action):
    """Envoie un e-mail en fin de workflow ou en cas d'alerte."""

    type_name = "send_email"
    label = "Envoyer un e-mail"
    category = "Système"

    @classmethod
    def param_specs(cls) -> list[ParamSpec]:
        return [
            ParamSpec("to", "Destinataire", "str", "", supports_vars=True,
                      placeholder="Ex : alerte@exemple.com"),
            ParamSpec("subject", "Sujet", "str", "", supports_vars=True,
                      placeholder="Ex : Rapport AutoFlow {{date}}"),
            ParamSpec("body", "Message", "text", "", supports_vars=True),
            ParamSpec("attachment", "Pièce jointe (optionnel)", "file", "",
                      supports_vars=True, placeholder="Ex : rapport.png"),
            ParamSpec("password_secret", "Secret du mot de passe SMTP", "str", "",
                      placeholder="Nom du secret (coffre)",
                      help="Le mot de passe est lu dans le coffre de secrets."),
        ]

    def validate(self) -> None:
        if not str(self.params.get("to", "")).strip():
            raise ValueError("Le destinataire ne peut pas être vide.")

    def execute(self, inputs: Any, windows: Any, context: dict[str, Any]) -> Any:
        self.validate()
        config = self._build_config(context)
        to = str(self._resolve(self.params.get("to", ""), context))
        subject = str(self._resolve(self.params.get("subject", ""), context))
        body = str(self._resolve(self.params.get("body", ""), context))
        attachment = str(self._resolve(self.params.get("attachment", ""), context)) or None
        sender = (context or {}).get("email_sender")  # injection pour tests
        log = (context or {}).get("log")
        try:
            email_smtp.send_email(config, to, subject, body, attachment, sender=sender)
        except Exception as exc:  # noqa: BLE001 — échec SMTP non fatal par défaut
            if callable(log):
                log(f"Échec d'envoi de l'e-mail : {exc}", "error")
            raise
        if callable(log):
            log(f"E-mail envoyé à {to}.", "info")
        return True

    def _build_config(self, context: dict[str, Any]) -> email_smtp.SmtpConfig:
        settings = (context or {}).get("settings")
        vault = (context or {}).get("secrets")
        password = ""
        secret_name = str(self.params.get("password_secret", "")).strip()
        if vault is not None and secret_name:
            try:
                password = vault.get(secret_name, "") or ""
            except Exception:  # noqa: BLE001
                password = ""
        return email_smtp.SmtpConfig(
            host=str(getattr(settings, "smtp_host", "") or ""),
            port=int(getattr(settings, "smtp_port", 587) or 587),
            username=str(getattr(settings, "smtp_username", "") or ""),
            password=password,
            use_tls=bool(getattr(settings, "smtp_use_tls", True)),
            sender=str(getattr(settings, "smtp_sender", "") or ""),
        )

    def summary(self) -> str:
        return f"Envoyer un e-mail à « {self.params.get('to')} »"
