import email
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.models import Submission
from app.services import email as email_module
from app.services.email import (
    ConsoleEmailService,
    Email,
    MemoryEmailService,
    OutboxEmailService,
    SMTPEmailService,
    build_email_service,
    send_safely,
)
from app.services.submissions import confirmation_email

SENDER = "Akshar <no-reply@example.org>"


def test_outbox_writes_a_valid_eml_file(tmp_path):
    service = OutboxEmailService(SENDER, tmp_path)
    service.send(Email(to="priya@example.com", subject="Hello", body="Namaste, Priya"))
    files = list(tmp_path.glob("*.eml"))
    assert len(files) == 1
    parsed = email.message_from_bytes(files[0].read_bytes())
    assert parsed["To"] == "priya@example.com"
    assert parsed["Subject"] == "Hello"
    assert "Namaste, Priya" in parsed.get_payload(decode=True).decode()


def test_memory_service_records_messages():
    service = MemoryEmailService(SENDER)
    service.send(Email(to="a@example.com", subject="S", body="B"))
    assert service.sent == [Email(to="a@example.com", subject="S", body="B")]


def test_header_injection_is_rejected():
    service = MemoryEmailService(SENDER)
    with pytest.raises(ValueError):
        service.send(Email(to="a@example.com", subject="Hi\nBcc: victim@example.com", body="x"))


def test_smtp_service_uses_tls_and_login(monkeypatch):
    smtp_instance = MagicMock()
    smtp_class = MagicMock()
    smtp_class.return_value.__enter__.return_value = smtp_instance
    monkeypatch.setattr(email_module.smtplib, "SMTP", smtp_class)

    service = SMTPEmailService(SENDER, "smtp.example.org", 587, "user", "pass", use_tls=True)
    service.send(Email(to="a@example.com", subject="S", body="B"))

    smtp_class.assert_called_once_with("smtp.example.org", 587, timeout=10)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user", "pass")
    smtp_instance.send_message.assert_called_once()


def test_send_safely_never_raises(caplog):
    class Broken(MemoryEmailService):
        def send(self, email):
            raise ConnectionError("SMTP down")

    send_safely(Broken(SENDER), Email(to="a@example.com", subject="S", body="B"))
    assert "Failed to send email" in caplog.text


@pytest.mark.parametrize(
    ("backend", "expected", "extra"),
    [
        ("console", ConsoleEmailService, {}),
        ("outbox", OutboxEmailService, {}),
        ("memory", MemoryEmailService, {}),
        ("smtp", SMTPEmailService, {"smtp_host": "smtp.example.org"}),
    ],
)
def test_backend_is_chosen_by_settings(backend, expected, extra):
    settings = Settings(_env_file=None, email_backend=backend, **extra)
    assert isinstance(build_email_service(settings), expected)


def test_smtp_backend_requires_a_host():
    with pytest.raises(ValueError, match="SMTP_HOST"):
        Settings(_env_file=None, email_backend="smtp")


def test_confirmation_emails_never_echo_the_message():
    sub = Submission(
        kind="contact",
        name="Rohan Gupta",
        email="r@example.com",
        topic="media",
        message="Buy cheap watches at spam.example",
        interests="",
    )
    mail = confirmation_email(sub, "http://localhost:8000")
    assert mail.to == "r@example.com"
    assert "Hi Rohan" in mail.body
    assert "Media and press" in mail.body
    assert "spam.example" not in mail.body


def test_volunteer_confirmation_lists_interests_and_availability():
    sub = Submission(
        kind="volunteer",
        name="Priya Sharma",
        email="p@example.com",
        message="x",
        interests="library,teaching",
        availability="weekends",
    )
    body = confirmation_email(sub, "http://localhost:8000").body
    assert "Teaching and tutoring" in body and "Libraries and reading" in body
    assert "Availability: Weekends" in body
