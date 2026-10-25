"""Read-side queries for events and posts. Routes stay thin; logic here is unit-testable."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import Event, Post

TAG_RE = re.compile(r"^[a-z0-9-]{1,40}$")


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


def get_event(session: Session, slug: str) -> Event | None:
    return session.scalar(select(Event).where(Event.slug == slug))


def latest_posts(session: Session, limit: int = 3):
    stmt = select(Post).where(Post.published_at <= utcnow()).order_by(Post.published_at.desc())
    return list(session.scalars(stmt.limit(limit)))


def get_post(session: Session, slug: str) -> Post | None:
    return session.scalar(select(Post).where(Post.slug == slug, Post.published_at <= utcnow()))


def _has_tag(tag: str):
    # Tags are stored as "a,b,c". Wrapping both sides in commas makes LIKE match whole
    # tags only ("data" must not match "metadata"). The value is a bound parameter.
    return (literal(",") + Post.tags + literal(",")).like(f"%,{tag},%")


@dataclass(frozen=True)
class Page:
    items: list
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page))


def paginate_posts(session: Session, page: int, per_page: int, tag: str | None = None) -> Page:
    conditions = [Post.published_at <= utcnow()]
    if tag:
        conditions.append(_has_tag(tag))
    total = session.scalar(select(func.count()).select_from(Post).where(*conditions)) or 0
    stmt = (
        select(Post)
        .where(*conditions)
        .order_by(Post.published_at.desc(), Post.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return Page(list(session.scalars(stmt)), page, per_page, total)


def tag_counts(session: Session) -> list[tuple[str, int]]:
    """All tags with post counts, most used first, then alphabetical."""
    counter: Counter[str] = Counter()
    for tags in session.scalars(select(Post.tags).where(Post.published_at <= utcnow())):
        counter.update(t for t in tags.split(",") if t)
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def posts_sharing_tags(session: Session, post: Post, limit: int = 3) -> list[Post]:
    """Non-ML fallback for related posts: most shared tags, then newest."""
    others = session.scalars(select(Post).where(Post.id != post.id, Post.published_at <= utcnow()))
    mine = set(post.tag_list)
    scored = [(len(mine & set(p.tag_list)), p.published_at, p) for p in others]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return [p for _, _, p in scored[:limit]]
