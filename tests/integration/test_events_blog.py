"""Stage (e): events (filter, detail, RSVP) and blog (pagination, tags, detail)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.db import utcnow
from app.models import Event, EventRSVP, Post
from app.seed_data import EVENTS, POSTS
from tests.helpers import form_tokens, submit

UPCOMING = "saturday-reading-mela-barmer"
PAST = "annual-impact-meet"
RSVP = {"name": "Kiran Joshi", "email": "kiran@example.com", "guests": "1"}
RSVP_URL = f"/events/{UPCOMING}/rsvp"


def rsvp_count(app) -> int:
    with app.state.db.session() as s:
        return s.scalar(select(func.count()).select_from(EventRSVP))


# --- Every page returns 200 -----------------------------------------------------

STATIC_PAGES = [
    "/",
    "/about",
    "/donate",
    "/volunteer",
    "/contact",
    "/events",
    "/events?when=past",
    "/blog",
    "/blog?page=2",
    "/blog?tag=literacy",
    "/thanks",
    "/styleguide",
    "/robots.txt",
    "/sitemap.xml",
    "/healthz",
]


@pytest.mark.parametrize("path", STATIC_PAGES)
def test_every_page_returns_200(client, seeded, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("slug", [e.slug for e in EVENTS])
def test_every_event_page_returns_200(client, seeded, slug):
    assert client.get(f"/events/{slug}").status_code == 200


@pytest.mark.parametrize("slug", [p.slug for p in POSTS])
def test_every_post_page_returns_200(client, seeded, slug):
    assert client.get(f"/blog/{slug}").status_code == 200


# --- Events ---------------------------------------------------------------------


def test_events_filter_upcoming_and_past(client, seeded):
    upcoming = client.get("/events").text
    past = client.get("/events?when=past").text
    assert "Saturday Reading Mela" in upcoming and "Annual impact meet" not in upcoming
    assert "Annual impact meet" in past and "Saturday Reading Mela" not in past
    assert 'href="/events?when=past" aria-current="page"' in past


def test_unknown_event_is_404(client, seeded):
    assert client.get("/events/no-such-event").status_code == 404


def test_event_calendar_export(client, seeded):
    response = client.get(f"/events/{UPCOMING}/calendar.ics")
    assert response.headers["content-type"].startswith("text/calendar")
    assert (
        "BEGIN:VEVENT" in response.text
        and "SUMMARY:Saturday Reading Mela\\, Barmer" in response.text
    )


def test_rsvp_happy_path(client, app, seeded):
    response = submit(client, RSVP_URL, RSVP, page=f"/events/{UPCOMING}")
    assert response.status_code == 303
    page = client.get(response.headers["location"].split("#")[0]).text
    assert "You&#39;re on the list, Kiran!" in page
    assert "58 of 60 places left" in page  # Kiran plus one guest
    assert rsvp_count(app) == 1
    [mail] = app.state.email_service.sent
    assert "Saturday Reading Mela" in mail.subject and "calendar.ics" in mail.body


def test_rsvp_same_email_twice_is_friendly_not_duplicated(client, app, seeded):
    submit(client, RSVP_URL, RSVP, page=f"/events/{UPCOMING}")
    submit(client, RSVP_URL, {**RSVP, "name": "Kiran J"}, page=f"/events/{UPCOMING}")
    assert rsvp_count(app) == 1
    assert "already on the list" in client.get(f"/events/{UPCOMING}").text


def test_rsvp_validation_errors(client, app, seeded):
    response = submit(
        client, RSVP_URL, {**RSVP, "email": "nope", "guests": "9"}, page=f"/events/{UPCOMING}"
    )
    assert response.status_code == 422
    assert "correct format" in response.text and "0 to 4" in response.text
    assert rsvp_count(app) == 0


def test_rsvp_closed_for_past_events(client, app, seeded):
    html = client.get(f"/events/{PAST}").text
    assert "This event has ended" in html and 'action="/events/' not in html
    tokens = form_tokens(client, f"/events/{UPCOMING}")
    response = client.post(f"/events/{PAST}/rsvp", data={**tokens, **RSVP}, follow_redirects=False)
    assert response.status_code == 409
    assert rsvp_count(app) == 0


def test_rsvp_respects_capacity(client, app, seeded):
    with app.state.db.session() as s:
        event = s.scalar(select(Event).where(Event.slug == UPCOMING))
        event.capacity = 2
        s.commit()
    response = submit(client, RSVP_URL, {**RSVP, "guests": "2"}, page=f"/events/{UPCOMING}")
    assert response.status_code == 409
    assert "Only 2 place(s) left" in response.text
    assert submit(client, RSVP_URL, RSVP, page=f"/events/{UPCOMING}").status_code == 303
    assert "fully booked" in client.get(f"/events/{UPCOMING}").text


def test_rsvp_requires_csrf(client, app, seeded):
    response = client.post(f"/events/{UPCOMING}/rsvp", data=RSVP)
    assert response.status_code == 403
    assert rsvp_count(app) == 0


# --- Blog -----------------------------------------------------------------------


def test_blog_pagination(client, seeded):
    first = client.get("/blog").text
    second = client.get("/blog?page=2").text
    assert first.count('class="card card--link"') == 5
    assert second.count('class="card card--link"') == len(POSTS) - 5
    assert 'rel="next"' in first and 'href="/blog?page=2"' in first
    assert 'rel="prev"' in second
    assert "noindex" in second and "noindex" not in first


@pytest.mark.parametrize(
    "query", ["?page=0", "?page=99", "?page=abc", "?tag=not-a-tag", "?tag=%3Cscript%3E"]
)
def test_blog_bad_queries_are_404(client, seeded, query):
    assert client.get("/blog" + query).status_code == 404


def test_blog_tag_filter_matches_whole_tags(client, seeded):
    html = client.get("/blog?tag=literacy").text
    tagged = [p for p in POSTS if "literacy" in p.tags]
    assert f"{len(tagged)} posts tagged" in html
    for post in tagged:
        assert post.title.replace("'", "&#39;") in html


def test_post_detail_has_reading_time_tags_and_related(client, seeded):
    html = client.get("/blog/how-meena-learned-to-read-in-90-days").text
    assert "min read" in html
    assert 'href="/blog?tag=literacy"' in html
    assert "You might also like" in html
    assert 'property="og:type" content="article"' in html


def test_post_markdown_is_sanitised(client, app, seeded):
    with app.state.db.session() as s:
        s.add(
            Post(
                slug="xss",
                title="XSS test",
                excerpt="x",
                author="Test",
                tags="test",
                body="Hello <script>alert(1)</script> [click](javascript:alert(1))",
                published_at=utcnow() - timedelta(days=1),
            )
        )
        s.commit()
    html = client.get("/blog/xss").text
    assert "<script>alert(1)</script>" not in html
    assert "javascript:" not in html


def test_future_posts_are_hidden(client, app, seeded):
    with app.state.db.session() as s:
        s.add(
            Post(
                slug="scheduled",
                title="Scheduled post",
                excerpt="x",
                author="Test",
                tags="",
                body="Soon",
                published_at=utcnow() + timedelta(days=3),
            )
        )
        s.commit()
    assert client.get("/blog/scheduled").status_code == 404
    assert "Scheduled post" not in client.get("/blog").text


def test_sitemap_lists_posts_and_events(client, seeded):
    xml = client.get("/sitemap.xml").text
    assert "/blog/how-meena-learned-to-read-in-90-days</loc><lastmod>" in xml
    assert f"/events/{UPCOMING}</loc>" in xml
