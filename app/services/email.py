"""Email delivery behind a small interface.

Routes depend on ``EmailService``, never on SMTP directly, so:
* local development writes .eml files to ./outbox (open them in any mail client),
* tests use ``MemoryEmailService`` and assert on what was "sent",
* production switches to SMTP with environment variables only, no code changes.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage as MimeMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.config import BASE_DIR, Settings

logger = logging.getLogger(__name__)

# Plain-text emails: no HTML autoescaping (it would turn "O'Brien" into "O&#39;Brien").
# Header injection is not possible because EmailMessage rejects newlines in headers.
_email_env = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates" / "emails"),
    autoescape=False,  # noqa: S701 - text/plain output, never rendered as HTML
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    body: str


def render_email(template: str, **context) -> str:
    return _email_env.get_template(template).render(**context)


class EmailService(ABC):
    def __init__(self, sender: str) -> None:
        self.sender = sender

    @abstractmethod
    def send(self, email: Email) -> None: ...

    def _to_mime(self, email: Email) -> MimeMessage:
        msg = MimeMessage()
        msg["From"] = self.sender
        msg["To"] = email.to
        msg["Subject"] = email.subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="akshar.example.org")
        msg.set_content(email.body)
        return msg


class ConsoleEmailService(EmailService):
    """Logs emails. Useful when you just want to see what would be sent."""

    def send(self, email: Email) -> None:
        logger.info("EMAIL to=%s subject=%r\n%s", email.to, email.subject, email.body)


class OutboxEmailService(EmailService):
    """Writes each email as an .eml file. The default in development."""

    def __init__(self, sender: str, directory: Path) -> None:
        super().__init__(sender)
        self.directory = directory

    def send(self, email: Email) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        name = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}.eml"
        (self.directory / name).write_bytes(bytes(self._to_mime(email)))
        logger.info("Email to %s written to %s", email.to, self.directory / name)


class MemoryEmailService(EmailService):
    """Keeps emails in a list. Used by the test suite."""

    def __init__(self, sender: str) -> None:
        super().__init__(sender)
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self._to_mime(email)  # still build the MIME message so header validation runs
        self.sent.append(email)


class SMTPEmailService(EmailService):
    def __init__(
        self,
        sender: str,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        timeout: float = 10,
    ) -> None:
        super().__init__(sender)
        self.host, self.port = host, port
        self.username, self.password = username, password
        self.use_tls, self.timeout = use_tls, timeout

    def send(self, email: Email) -> None:
        with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as smtp:
            if self.use_tls:
                smtp.starttls(context=ssl.create_default_context())
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(self._to_mime(email))


def build_email_service(settings: Settings) -> EmailService:
    sender = settings.email_from
    match settings.email_backend:
        case "console":
            return ConsoleEmailService(sender)
        case "memory":
            return MemoryEmailService(sender)
        case "smtp":
            return SMTPEmailService(
                sender,
                host=settings.smtp_host or "",
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password.get_secret_value()
                if settings.smtp_password
                else None,
                use_tls=settings.smtp_use_tls,
            )
        case _:
            return OutboxEmailService(sender, settings.outbox_dir)


def send_safely(service: EmailService, email: Email) -> None:
    """Run as a background task: a mail outage must never lose the saved submission."""
    try:
        service.send(email)
    except Exception:
        logger.exception("Failed to send email to %s", email.to)
