"""Small, pure display helpers used by templates and emails."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime, timedelta, timezone

# India has no daylight saving, so a fixed offset is exact and avoids needing tzdata on Windows.
IST = timezone(timedelta(hours=5, minutes=30), "IST")

_WORD_RE = re.compile(r"\w+")


def format_inr(amount: int | float, *, symbol: bool = True) -> str:
    """Format a rupee amount with Indian digit grouping: 1250000 -> "₹12,50,000"."""
    digits = str(round(amount))
    sign = ""
    if digits.startswith("-"):
        sign, digits = "-", digits[1:]
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join([*groups, tail])
    return f"{sign}{'₹' if symbol else ''}{digits}"


def format_compact_number(value: int) -> str:
    """Impact stats: 12400 -> "12,400". Kept separate so the format can change in one place."""
    return f"{value:,}"


def to_ist(dt: datetime) -> datetime:
    """Convert a naive-UTC datetime from the DB to India time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def format_date(dt: datetime, fmt: str = "%d %b %Y") -> str:
    return to_ist(dt).strftime(fmt).lstrip("0")


def format_datetime(dt: datetime) -> str:
    local = to_ist(dt)
    hour = local.strftime("%I").lstrip("0")
    return f"{local.strftime('%a %d %b %Y').replace(' 0', ' ')}, {hour}:{local:%M} {local:%p} IST"


def reading_time_minutes(text: str, words_per_minute: int = 200) -> int:
    """Estimated reading time, never less than one minute."""
    words = len(_WORD_RE.findall(text))
    return max(1, math.ceil(words / words_per_minute))
