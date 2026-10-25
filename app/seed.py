"""Seed demo events and blog posts.

Usage:
    python -m app.seed           # insert demo content into empty tables (safe to re-run)
    python -m app.seed --reset   # drop every table, recreate and seed (deletes submissions too)
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, Database, utcnow
from app.formatting import IST
from app.models import Event, Post, join_tags
from app.seed_data import EVENTS, POSTS, EventSeed

logger = logging.getLogger(__name__)


def event_start(seed: EventSeed, now: datetime) -> datetime:
    """Resolve a relative event date to a naive-UTC start time."""
    local_day = now.replace(tzinfo=UTC).astimezone(IST).date() + timedelta(days=seed.days_from_now)
    if seed.weekday is not None:
        local_day += timedelta(days=(seed.weekday - local_day.weekday()) % 7)
    hour, minute = seed.start
    local = datetime(local_day.year, local_day.month, local_day.day, hour, minute, tzinfo=IST)
    return local.astimezone(UTC).replace(tzinfo=None)


def seed(session: Session, now: datetime | None = None) -> dict[str, int]:
    """Insert demo content into empty tables. Returns how many rows were added per table."""
    now = now or utcnow()
    added = {"events": 0, "posts": 0}

    if session.scalar(select(func.count()).select_from(Event)) == 0:
        for e in EVENTS:
            starts = event_start(e, now)
            session.add(
                Event(
                    slug=e.slug,
                    title=e.title,
                    summary=e.summary,
                    body=e.body,
                    location=e.location,
                    is_online=e.is_online,
                    starts_at=starts,
                    ends_at=starts + timedelta(hours=e.duration_hours),
                    tags=join_tags(e.tags),
                    capacity=e.capacity,
                    image=e.image,
                    image_alt=e.image_alt,
                )
            )
        added["events"] = len(EVENTS)

    if session.scalar(select(func.count()).select_from(Post)) == 0:
        for p in POSTS:
            session.add(
                Post(
                    slug=p.slug,
                    title=p.title,
                    excerpt=p.excerpt,
                    body=p.body,
                    author=p.author,
                    author_role=p.author_role,
                    tags=join_tags(p.tags),
                    image=p.image,
                    image_alt=p.image_alt,
                    published_at=(now - timedelta(days=p.days_ago)).replace(
                        hour=4, minute=30, second=0, microsecond=0
                    ),
                )
            )
        added["posts"] = len(POSTS)

    session.commit()
    return added


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    db = Database(get_settings().database_url)
    if args.reset:
        Base.metadata.drop_all(db.engine)
    db.create_all()
    with db.session() as session:
        added = seed(session)
    for table, count in added.items():
        logger.info("%s: %s", table, f"added {count}" if count else "already seeded, skipped")


if __name__ == "__main__":
    main()
