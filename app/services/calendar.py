"""Minimal iCalendar (RFC 5545) export so visitors can add an event to their calendar."""

from __future__ import annotations

from app.config import BRAND
from app.db import utcnow
from app.models import Event


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", r"\;").replace(",", "\\,").replace("\n", "\\n")


def event_to_ics(event: Event, url: str) -> str:
    fmt = "%Y%m%dT%H%M%SZ"  # stored times are UTC, so use the UTC "Z" form
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{BRAND.name}//Events//EN",
        "BEGIN:VEVENT",
        f"UID:event-{event.id}@akshar.example.org",
        f"DTSTAMP:{utcnow().strftime(fmt)}",
        f"DTSTART:{event.starts_at.strftime(fmt)}",
        f"DTEND:{event.ends_at.strftime(fmt)}",
        f"SUMMARY:{_escape(event.title)}",
        f"DESCRIPTION:{_escape(event.summary + ' ' + url)}",
        f"LOCATION:{_escape(event.location)}",
        f"URL:{url}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"
