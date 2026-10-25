from datetime import datetime

from sqlalchemy import func, select

from app.formatting import to_ist
from app.models import Event, Post
from app.seed import event_start, seed
from app.seed_data import EVENTS, POSTS


def test_seed_meets_minimum_content_requirements():
    assert len(EVENTS) >= 5
    assert len(POSTS) >= 6
    assert len({e.slug for e in EVENTS}) == len(EVENTS)
    assert len({p.slug for p in POSTS}) == len(POSTS)


def test_seed_is_idempotent(db_session):
    first = seed(db_session)
    second = seed(db_session)
    assert first == {"events": len(EVENTS), "posts": len(POSTS)}
    assert second == {"events": 0, "posts": 0}
    assert db_session.scalar(select(func.count()).select_from(Event)) == len(EVENTS)
    assert db_session.scalar(select(func.count()).select_from(Post)) == len(POSTS)


def test_seed_creates_both_upcoming_and_past_events(db_session):
    now = datetime(2026, 1, 1, 12, 0)
    seed(db_session, now=now)
    events = list(db_session.scalars(select(Event)))
    assert any(e.starts_at > now for e in events)
    assert any(e.ends_at < now for e in events)


def test_event_start_lands_on_requested_weekday_and_local_time():
    saturday_event = next(e for e in EVENTS if e.weekday == 5)
    start = event_start(saturday_event, datetime(2026, 1, 1, 12, 0))  # a Thursday
    local = to_ist(start)
    assert local.weekday() == 5
    assert (local.hour, local.minute) == saturday_event.start
