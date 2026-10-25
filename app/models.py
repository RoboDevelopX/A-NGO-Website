"""SQLAlchemy models.

Conventions:
* Datetimes are naive UTC (see ``app.db.utcnow``) and converted to IST only for display.
* Small lists (tags, interests) are stored as comma-separated text. SQLite has no array
  type, the lists are short, and we never query inside them except with LIKE in admin
  search. A join table would be the right call at a larger scale.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow


def split_tags(value: str | None) -> list[str]:
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def join_tags(tags: list[str] | tuple[str, ...] | set[str]) -> str:
    # Sorted + de-duplicated so the stored value is stable regardless of input order.
    return ",".join(sorted({t.strip().lower() for t in tags if t.strip()}))


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(400))
    body: Mapped[str] = mapped_column(Text)  # Markdown, sanitised when rendered
    location: Mapped[str] = mapped_column(String(200))
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    tags: Mapped[str] = mapped_column(String(300), default="")
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image: Mapped[str] = mapped_column(String(200), default="")
    image_alt: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    rsvps: Mapped[list[EventRSVP]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def tag_list(self) -> list[str]:
        return split_tags(self.tags)

    @property
    def seats_taken(self) -> int:
        return sum(1 + r.guests for r in self.rsvps)

    @property
    def seats_left(self) -> int | None:
        return None if self.capacity is None else max(0, self.capacity - self.seats_taken)

    @property
    def short_location(self) -> str:
        """Shorten "Hall 2, Barmer, Rajasthan" to "Barmer, Rajasthan" for compact cards."""
        if self.is_online:
            return "Online"
        parts = [p.strip() for p in self.location.split(",")]
        return ", ".join(parts[-2:])

    def is_past(self, now: datetime | None = None) -> bool:
        return self.ends_at < (now or utcnow())


class EventRSVP(Base):
    __tablename__ = "event_rsvps"
    # One RSVP per email per event; the database enforces it, not just the form.
    __table_args__ = (UniqueConstraint("event_id", "email", name="uq_rsvp_event_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254))
    guests: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped[Event] = relationship(back_populates="rsvps")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    excerpt: Mapped[str] = mapped_column(String(400))
    body: Mapped[str] = mapped_column(Text)  # Markdown, sanitised when rendered
    author: Mapped[str] = mapped_column(String(120))
    author_role: Mapped[str] = mapped_column(String(120), default="")
    tags: Mapped[str] = mapped_column(String(300), default="")
    image: Mapped[str] = mapped_column(String(200), default="")
    image_alt: Mapped[str] = mapped_column(String(300), default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    @property
    def tag_list(self) -> list[str]:
        return split_tags(self.tags)


class Submission(Base):
    """A volunteer sign-up or a contact message. One table, distinguished by ``kind``."""

    __tablename__ = "submissions"

    STATUSES = ("new", "contacted", "archived")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)  # "volunteer" | "contact"
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interests: Mapped[str] = mapped_column(String(300), default="")
    availability: Mapped[str | None] = mapped_column(String(30), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(30), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    spam_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # A keyed hash, not the raw IP: enough to spot abuse patterns, useless if leaked.
    ip_hash: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    @property
    def interest_list(self) -> list[str]:
        return split_tags(self.interests)


class FormToken(Base):
    """One-time form nonces. A unique primary key makes duplicate submits fail atomically."""

    __tablename__ = "form_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Donation(Base):
    """A *mock* donation. There are deliberately no card-related columns."""

    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    frequency: Mapped[str] = mapped_column(String(20))  # "one_time" | "monthly"
    donor_name: Mapped[str] = mapped_column(String(80))
    donor_email: Mapped[str] = mapped_column(String(254))
    provider: Mapped[str] = mapped_column(String(30))
    provider_ref: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), index=True)  # "succeeded" | "declined"
    failure_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # The form nonce: a unique key means a double-clicked Donate button records one gift.
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    @property
    def amount_rupees(self) -> int:
        return self.amount_paise // 100
