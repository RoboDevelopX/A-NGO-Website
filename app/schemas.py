"""Server-side validation for public forms.

Design notes:
* Every rule raises a ``PydanticCustomError`` with copy written for people, so the error
  shown next to a field is never pydantic's default ("String should have at least...").
* Errors pydantic raises on its own (missing field, bad enum value) are mapped to the same
  friendly per-field copy in ``friendly_errors``.
* The same copy is passed to the templates as data attributes, so client-side validation
  in static/js/forms.js shows exactly the same words as the server.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from typing import Any, ClassVar

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from pydantic_core import PydanticCustomError


class Interest(StrEnum):
    TEACHING = "teaching"
    MENTORING = "mentoring"
    DIGITAL = "digital"
    LIBRARY = "library"
    EVENTS = "events"
    FUNDRAISING = "fundraising"
    CONTENT = "content"


class Availability(StrEnum):
    WEEKDAY_DAYTIME = "weekday_daytime"
    WEEKDAY_EVENINGS = "weekday_evenings"
    WEEKENDS = "weekends"
    FLEXIBLE = "flexible"
    REMOTE = "remote"


class ContactTopic(StrEnum):
    GENERAL = "general"
    PARTNERSHIP = "partnership"
    MEDIA = "media"
    DONATION = "donation"
    OTHER = "other"


# (label, hint) for each interest. The keys double as event tags for volunteer matching.
INTEREST_LABELS: dict[Interest, tuple[str, str]] = {
    Interest.TEACHING: ("Teaching and tutoring", "Reading and maths with small groups"),
    Interest.MENTORING: ("Mentoring girls", "Fortnightly circles for girls in Classes 8 to 10"),
    Interest.DIGITAL: ("Digital literacy and coding", "Tablets, Scratch and Code Clubs"),
    Interest.LIBRARY: ("Libraries and reading", "Sorting books, read-alouds, library days"),
    Interest.EVENTS: ("Event support", "Melas, camps, walks and open houses"),
    Interest.FUNDRAISING: ("Fundraising and outreach", "Campaigns, the annual walk, CSR"),
    Interest.CONTENT: ("Writing, photos and social media", "Stories from the field"),
}

AVAILABILITY_LABELS: dict[Availability, str] = {
    Availability.WEEKDAY_DAYTIME: "Weekday daytime",
    Availability.WEEKDAY_EVENINGS: "Weekday evenings (after 5 PM)",
    Availability.WEEKENDS: "Weekends",
    Availability.FLEXIBLE: "Flexible, any time",
    Availability.REMOTE: "Remote only",
}

TOPIC_LABELS: dict[ContactTopic, str] = {
    ContactTopic.GENERAL: "General question",
    ContactTopic.PARTNERSHIP: "Partnerships and CSR",
    ContactTopic.MEDIA: "Media and press",
    ContactTopic.DONATION: "A question about a donation",
    ContactTopic.OTHER: "Something else",
}

NAME_MAX, EMAIL_MAX, PHONE_MAX, MESSAGE_MAX = 80, 254, 20, 2000
VOLUNTEER_MESSAGE_MIN, CONTACT_MESSAGE_MIN = 20, 10

_NAME_PUNCTUATION = set(" .'’-")
_PHONE_RE = re.compile(r"^\+?[0-9\s\-()]+$")

# Per-field fallback copy for errors pydantic raises itself (missing field, invalid choice).
FIELD_MESSAGES: dict[str, str] = {
    "name": "Enter your full name",
    "email": "Enter your email address",
    "phone": "Enter a phone number with 7 to 15 digits, like +91 98765 43210",
    "interests": "Choose at least one way you'd like to help",
    "availability": "Choose when you're usually available",
    "topic": "Choose what your message is about",
    "message": "Enter your message",
}

# Copy shared with client-side validation (rendered as data-msg-* attributes).
CLIENT_MESSAGES: dict[str, dict[str, str]] = {
    "name": {"required": FIELD_MESSAGES["name"], "invalid": "Name must be 2 to 80 letters"},
    "email": {
        "required": FIELD_MESSAGES["email"],
        "invalid": "Enter an email address in the correct format, like name@example.com",
    },
    "phone": {"invalid": FIELD_MESSAGES["phone"]},
    "interests": {"required": FIELD_MESSAGES["interests"]},
    "availability": {"required": FIELD_MESSAGES["availability"]},
    "topic": {"required": FIELD_MESSAGES["topic"]},
    "message": {
        "required": FIELD_MESSAGES["message"],
        "volunteer_short": f"Tell us a little more (at least {VOLUNTEER_MESSAGE_MIN} characters)",
        "contact_short": f"Your message must be at least {CONTACT_MESSAGE_MIN} characters",
        "long": f"Keep your message under {MESSAGE_MAX} characters",
    },
}


def _looks_like_name(name: str) -> bool:
    """Letters and combining marks from any script, plus space . ' ’ -

    Unicode categories rather than a regex: the regex word class misses vowel signs (Mc/Mn)
    in Devanagari, so "प्रिया" would be rejected as an invalid name.
    """
    if not unicodedata.category(name[0]).startswith("L"):
        return False
    return all(unicodedata.category(ch)[0] in "LM" or ch in _NAME_PUNCTUATION for ch in name)


def _err(kind: str, message: str) -> PydanticCustomError:
    return PydanticCustomError(f"friendly_{kind}", message)


def clean_text(value: Any, *, multiline: bool = False) -> str:
    """Normalise user text: NFC, no control characters, tidy whitespace.

    We store what people typed (minus invisible junk) and escape on output. Escaping on
    input instead would double-escape in templates and corrupt the CSV export.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value)).replace("\r\n", "\n").replace("\r", "\n")
    if not multiline:
        text = text.replace("\n", " ").replace("\t", " ")
    allowed = {"\n", "\t"} if multiline else set()
    # Category C = control, format (e.g. zero-width spaces), private use and unassigned.
    text = "".join(ch for ch in text if ch in allowed or unicodedata.category(ch)[0] != "C")
    if multiline:
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()
    return re.sub(r"\s+", " ", text).strip()


class _PersonForm(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: str
    phone: str | None = None
    message: str

    # Subclasses override these; ClassVar keeps them out of the validated fields.
    message_min: ClassVar[int] = VOLUNTEER_MESSAGE_MIN
    message_short_copy: ClassVar[str] = CLIENT_MESSAGES["message"]["volunteer_short"]

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str:
        name = clean_text(value)
        if not name:
            raise _err("required", FIELD_MESSAGES["name"])
        if len(name) < 2 or len(name) > NAME_MAX or not _looks_like_name(name):
            raise _err(
                "name",
                "Name must be 2 to 80 letters, and can include spaces, apostrophes, "
                "hyphens and full stops",
            )
        return name

    @field_validator("email", mode="before")
    @classmethod
    def _validate_email(cls, value: Any) -> str:
        email = clean_text(value)
        if not email:
            raise _err("required", FIELD_MESSAGES["email"])
        if len(email) > EMAIL_MAX:
            raise _err("email", CLIENT_MESSAGES["email"]["invalid"])
        try:
            # No DNS lookup: keeps validation fast, offline and deterministic in tests.
            result = validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise _err("email", CLIENT_MESSAGES["email"]["invalid"]) from None
        return result.normalized

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: Any) -> str | None:
        phone = clean_text(value)
        if not phone:
            return None
        digits = re.sub(r"\D", "", phone)
        if len(phone) > PHONE_MAX or not _PHONE_RE.match(phone) or not 7 <= len(digits) <= 15:
            raise _err("phone", FIELD_MESSAGES["phone"])
        return phone

    @field_validator("message", mode="before")
    @classmethod
    def _validate_message(cls, value: Any) -> str:
        message = clean_text(value, multiline=True)
        if not message:
            raise _err("required", FIELD_MESSAGES["message"])
        if len(message) < cls.message_min:
            raise _err("message_short", cls.message_short_copy)
        if len(message) > MESSAGE_MAX:
            raise _err("message_long", CLIENT_MESSAGES["message"]["long"])
        return message


class VolunteerForm(_PersonForm):
    interests: list[Interest]
    availability: Availability

    @field_validator("interests", mode="before")
    @classmethod
    def _validate_interests(cls, value: Any) -> list[str]:
        items = value if isinstance(value, list | tuple) else ([value] if value else [])
        unique = list(dict.fromkeys(str(v) for v in items if v))
        if not unique:
            raise _err("required", FIELD_MESSAGES["interests"])
        return unique


class ContactForm(_PersonForm):
    topic: ContactTopic

    message_min: ClassVar[int] = CONTACT_MESSAGE_MIN
    message_short_copy: ClassVar[str] = CLIENT_MESSAGES["message"]["contact_short"]


def friendly_errors(exc: ValidationError) -> dict[str, str]:
    """Map a ValidationError to {field: message}, one message per field, in field order."""
    errors: dict[str, str] = {}
    for error in exc.errors():
        field = str(error["loc"][0]) if error["loc"] else "form"
        if field in errors:
            continue
        if error["type"].startswith("friendly_"):
            errors[field] = error["msg"]
        else:
            errors[field] = FIELD_MESSAGES.get(field, "Check this field")
    return errors
