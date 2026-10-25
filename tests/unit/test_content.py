from datetime import datetime, timedelta

from app.db import utcnow
from app.models import Event, Post
from app.services.calendar import event_to_ics
from app.services.content import paginate_posts, posts_sharing_tags, tag_counts
from app.services.markdown import render_markdown


def make_post(slug: str, tags: str, days_ago: int = 1) -> Post:
    return Post(
        slug=slug, title=slug.title(), excerpt="x", body="word " * 10, author="A",
        tags=tags, published_at=utcnow() - timedelta(days=days_ago),
    )  # fmt: skip


def test_tag_filter_matches_whole_tags_only(db_session):
    db_session.add_all(
        [make_post("a", "data,impact"), make_post("b", "metadata"), make_post("c", "")]
    )
    db_session.commit()
    page = paginate_posts(db_session, page=1, per_page=10, tag="data")
    assert [p.slug for p in page.items] == ["a"]


def test_pagination_maths(db_session):
    db_session.add_all([make_post(f"p{i}", "t", days_ago=i) for i in range(1, 8)])
    db_session.commit()
    page2 = paginate_posts(db_session, page=2, per_page=3)
    assert (page2.total, page2.total_pages) == (7, 3)
    assert [p.slug for p in page2.items] == ["p4", "p5", "p6"]  # newest first


def test_tag_counts_sorted_by_popularity(db_session):
    db_session.add_all([make_post("a", "x,y"), make_post("b", "y"), make_post("c", "y,z")])
    db_session.commit()
    assert tag_counts(db_session) == [("y", 3), ("x", 1), ("z", 1)]


def test_related_fallback_prefers_most_shared_tags(db_session):
    target = make_post("target", "a,b,c")
    db_session.add_all(
        [target, make_post("two", "a,b", 5), make_post("one", "c", 1), make_post("none", "z")]
    )
    db_session.commit()
    assert [p.slug for p in posts_sharing_tags(db_session, target)] == ["two", "one"]


def test_markdown_renders_tables_and_strips_dangerous_html():
    html = render_markdown("| a |\n| - |\n| 1 |\n\n<img src=x onerror=alert(1)> <b>ok</b>")
    assert "<table>" in html
    assert "onerror" not in html and "<img" not in html


def test_ics_escapes_special_characters():
    event = Event(
        id=1, slug="e", title="Walk, talk; learn", summary="Fun", body="", location="Jaipur, RJ",
        starts_at=datetime(2026, 1, 3, 3, 30), ends_at=datetime(2026, 1, 3, 6, 30), tags="",
    )  # fmt: skip
    ics = event_to_ics(event, "https://example.org/events/e")
    assert "SUMMARY:Walk\\, talk\\; learn" in ics
    assert "DTSTART:20260103T033000Z" in ics
    assert ics.endswith("\r\n")
