"""Read-side queries for events and posts. Routes stay thin; logic here is unit-testable."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import Event, Post


def upcoming_events(session: Session, limit: int | None = None, now: datetime | None = None):
    stmt = select(Event).where(Event.ends_at >= (now or utcnow())).order_by(Event.starts_at)
    if limit:
        stmt = stmt.limit(limit)
    return list(session.scalars(stmt))


def past_events(session: Session, limit: int | None = None, now: datetime | None = None):
    stmt = select(Event).where(Event.ends_at < (now or utcnow())).order_by(Event.starts_at.desc())
    if limit:
        stmt = stmt.limit(limit)
    return list(session.scalars(stmt))


def latest_posts(session: Session, limit: int = 3):
    stmt = select(Post).where(Post.published_at <= utcnow()).order_by(Post.published_at.desc())
    return list(session.scalars(stmt.limit(limit)))
