"""Stage (b): homepage and About page."""

from __future__ import annotations

from app.content import FUNDS_BREAKDOWN, GALLERY, TESTIMONIALS
from app.seed_data import POSTS


def test_home_shows_hero_ctas_and_sections(client, seeded):
    html = client.get("/").text
    assert 'href="/donate"' in html and 'href="/volunteer"' in html
    for heading in ["Our impact so far", "What we do", "Life at our centres", "Upcoming events"]:
        assert heading in html


def test_home_pulls_upcoming_events_and_latest_posts_from_db(client, seeded):
    html = client.get("/").text
    assert "Saturday Reading Mela, Barmer" in html  # nearest upcoming event
    assert "Annual impact meet" not in html  # past events are excluded
    newest_post = min(POSTS, key=lambda p: p.days_ago)
    assert newest_post.title in html


def test_home_handles_empty_database(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "No events are scheduled right now" in response.text


def test_every_image_on_home_has_alt_text(client, seeded):
    html = client.get("/").text
    for item in [*GALLERY, *TESTIMONIALS]:
        alt = item.alt if hasattr(item, "alt") else item.image_alt
        assert f'alt="{alt}"' in html.replace("&#39;", "'")
    assert "<img" in html and 'alt=""' not in html


def test_stats_render_final_values_without_js(client):
    html = client.get("/").text
    assert 'data-count-to="12400"' in html
    assert "12,400" in html


def test_about_page_sections(client):
    html = client.get("/about").text
    for heading in [
        "Why we exist",
        "Our values",
        "Our approach",
        "Milestones",
        "Our team",
        "How funds are used",
    ]:
        assert heading in html
    assert 'id="funds"' in html


def test_funds_breakdown_adds_up_to_100():
    assert sum(line.percent for line in FUNDS_BREAKDOWN) == 100


def test_nav_marks_current_page(client):
    html = client.get("/about").text
    assert '<a href="/about" aria-current="page">About</a>' in html
