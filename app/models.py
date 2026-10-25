"""SQLAlchemy models.

Conventions:
* Datetimes are naive UTC (see ``app.db.utcnow``) and converted to IST only for display.
* Small lists (tags, interests) are stored as comma-separated text. SQLite has no array
  type, the lists are short, and we never query inside them except with LIKE in admin
  search. A join table would be the right call at a larger scale.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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

    @property
    def tag_list(self) -> list[str]:
        return split_tags(self.tags)

    @property
    def short_location(self) -> str:
        """Shorten "Hall 2, Barmer, Rajasthan" to "Barmer, Rajasthan" for compact cards."""
        if self.is_online:
            return "Online"
        parts = [p.strip() for p in self.location.split(",")]
        return ", ".join(parts[-2:])

    def is_past(self, now: datetime | None = None) -> bool:
        return self.ends_at < (now or utcnow())


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
