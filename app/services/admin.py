"""Admin queries, authentication and CSV export."""

from __future__ import annotations

import csv
import hmac
import io
from collections.abc import Iterable
from dataclasses import dataclass

import bcrypt
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Donation, EventRSVP, Submission

STATUS_FILTERS = ("all", *Submission.STATUSES)
KIND_FILTERS = ("all", "volunteer", "contact")
SPAM_FILTERS = ("hide", "only", "include")

# A real bcrypt hash of a random string. When the username is wrong we still run
# checkpw against this, so a wrong username takes as long as a wrong password and
# response times don't reveal which usernames exist.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())


def verify_admin(settings: Settings, username: str, password: str) -> bool:
    if settings.admin_password_hash is None:
        return False
    stored = settings.admin_password_hash.get_secret_value().encode()
    user_ok = hmac.compare_digest(username.encode(), settings.admin_username.encode())
    try:
        password_ok = bcrypt.checkpw(password.encode(), stored if user_ok else _DUMMY_HASH)
    except ValueError:  # malformed hash in the environment
        return False
    return user_ok and password_ok


@dataclass(frozen=True)
class SubmissionFilters:
    q: str = ""
    status: str = "all"
    kind: str = "all"
    spam: str = "hide"

    @classmethod
    def from_query(cls, q=None, status=None, kind=None, spam=None) -> SubmissionFilters:
        # Unknown values fall back to defaults instead of erroring: it's an internal tool.
        return cls(
            q=(q or "").strip()[:100],
            status=status if status in STATUS_FILTERS else "all",
            kind=kind if kind in KIND_FILTERS else "all",
            spam=spam if spam in SPAM_FILTERS else "hide",
        )

    def as_params(self) -> dict[str, str]:
        defaults = SubmissionFilters()
        return {k: v for k, v in vars(self).items() if v and v != getattr(defaults, k)}


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def filtered_query(filters: SubmissionFilters):
    stmt = select(Submission)
    if filters.q:
        pattern = f"%{_escape_like(filters.q)}%"
        stmt = stmt.where(
            or_(
                Submission.name.ilike(pattern, escape="\\"),
                Submission.email.ilike(pattern, escape="\\"),
                Submission.message.ilike(pattern, escape="\\"),
                Submission.interests.ilike(pattern, escape="\\"),
            )
        )
    if filters.status != "all":
        stmt = stmt.where(Submission.status == filters.status)
    if filters.kind != "all":
        stmt = stmt.where(Submission.kind == filters.kind)
    if filters.spam == "hide":
        stmt = stmt.where(Submission.is_spam.is_(False))
    elif filters.spam == "only":
        stmt = stmt.where(Submission.is_spam.is_(True))
    return stmt.order_by(Submission.created_at.desc(), Submission.id.desc())


def list_submissions(db: Session, filters: SubmissionFilters, page: int, per_page: int):
    stmt = filtered_query(filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)))
    return items, total


def dashboard_stats(db: Session) -> dict[str, int]:
    by_status = dict(
        db.execute(
            select(Submission.status, func.count())
            .where(Submission.is_spam.is_(False))
            .group_by(Submission.status)
        ).all()
    )
    return {
        "new": by_status.get("new", 0),
        "contacted": by_status.get("contacted", 0),
        "archived": by_status.get("archived", 0),
        "spam": db.scalar(select(func.count()).where(Submission.is_spam.is_(True))) or 0,
        "donations": db.scalar(
            select(func.count()).select_from(Donation).where(Donation.status == "succeeded")
        )
        or 0,
        "donated_rupees": (
            db.scalar(
                select(func.coalesce(func.sum(Donation.amount_paise), 0)).where(
                    Donation.status == "succeeded"
                )
            )
            or 0
        )
        // 100,
        "rsvps": db.scalar(select(func.count()).select_from(EventRSVP)) or 0,
    }


# Spreadsheet apps execute cells that start with these characters as formulas, so a
# visitor could type "=HYPERLINK(...)" into a form and attack whoever opens the export.
# OWASP's recommendation is to prefix such cells with a single quote.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


CSV_COLUMNS = [
    "id", "created_at", "kind", "status", "name", "email", "phone", "interests",
    "availability", "topic", "message", "is_spam", "spam_score",
]  # fmt: skip


def submissions_csv(rows: Iterable[Submission]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([csv_safe(getattr(row, col)) for col in CSV_COLUMNS])
    # Excel needs a BOM to open UTF-8 (e.g. Devanagari names) correctly.
    return "﻿" + buffer.getvalue()
