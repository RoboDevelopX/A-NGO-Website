"""Stage (g): the three ML features working inside the site, and their fallbacks."""

from __future__ import annotations

import bcrypt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.main import create_app
from app.ml.spam import save_model, train
from app.ml.spam_data import generate_dataset
from app.models import Post, Submission
from app.services.content import posts_sharing_tags
from app.services.ml import TfidfRelatedPosts
from tests.helpers import VALID_CONTACT, VALID_VOLUNTEER, submit

SPAM_CONTACT = {
    **VALID_CONTACT,
    "name": "SEO Expert",
    "email": "seo@example.com",
    "message": "Want your website on the first page of Google? We offer backlinks at the "
    "lowest price. Visit http://rank1-google.info now!",
}


@pytest.fixture(scope="session")
def model_path(tmp_path_factory):
    """A small model trained once for the whole test run (well under a second)."""
    path = tmp_path_factory.mktemp("model") / "spam_model.joblib"
    save_model(train(generate_dataset(n_per_class=300)), path)
    return path


@pytest.fixture
def ml_app(settings, model_path):
    update = {"ml_spam_filter": True, "spam_model_path": model_path}
    return create_app(settings.model_copy(update=update))


@pytest.fixture
def ml_client(ml_app):
    with TestClient(ml_app) as client:
        yield client


def _only_submission(app) -> Submission:
    with app.state.db.session() as s:
        return s.scalars(select(Submission)).one()


# --- Spam classifier -------------------------------------------------------------


def test_spam_is_saved_flagged_and_not_emailed(ml_client, ml_app):
    assert ml_app.state.spam_filter.enabled
    response = submit(ml_client, "/contact", SPAM_CONTACT)
    # The sender sees the normal success page; nothing tells a bot it was caught.
    assert response.status_code == 303 and response.headers["location"] == "/thanks"
    sub = _only_submission(ml_app)
    assert sub.is_spam is True and sub.spam_score >= ml_app.state.spam_filter.threshold
    assert ml_app.state.email_service.sent == []


def test_genuine_message_is_scored_accepted_and_emailed(ml_client, ml_app):
    submit(ml_client, "/volunteer", VALID_VOLUNTEER)
    sub = _only_submission(ml_app)
    assert sub.is_spam is False and 0 <= sub.spam_score < ml_app.state.spam_filter.threshold
    assert len(ml_app.state.email_service.sent) == 1


def test_flagged_items_are_hidden_from_admin_by_default(settings, model_path):
    password = "correct horse battery staple"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()
    app = create_app(
        settings.model_copy(
            update={
                "ml_spam_filter": True,
                "spam_model_path": model_path,
                "admin_password_hash": SecretStr(hashed),
            }
        )
    )
    with TestClient(app) as client:
        submit(client, "/contact", SPAM_CONTACT)
        page = client.get("/admin/login").text
        token = page.split('name="csrf_token" value="')[1].split('"')[0]
        client.post(
            "/admin/login", data={"csrf_token": token, "username": "admin", "password": password}
        )
        assert "SEO Expert" not in client.get("/admin").text
        spam_view = client.get("/admin?spam=only").text
        assert "SEO Expert" in spam_view and "Spam " in spam_view


def test_without_a_model_every_submission_is_accepted_unscored(client, app):
    assert not app.state.spam_filter.enabled  # conftest points at a missing file
    submit(client, "/contact", SPAM_CONTACT)
    sub = _only_submission(app)
    assert sub.is_spam is False and sub.spam_score is None
    assert len(app.state.email_service.sent) == 1


# --- Volunteer to event matching -------------------------------------------------


def test_thanks_page_suggests_matching_events_with_reasons(client, seeded):
    submit(client, "/volunteer", VALID_VOLUNTEER)  # teaching + library, weekends
    html = client.get("/thanks").text
    assert "Events that match your interests" in html
    assert "Why we suggested this" in html
    assert "Matches your interest in" in html


def test_thanks_page_falls_back_to_upcoming_events_when_matching_is_off(settings):
    app = create_app(settings.model_copy(update={"ml_event_matching": False}))
    with TestClient(app) as client:
        from app.seed import seed

        with app.state.db.session() as s:
            seed(s)
        submit(client, "/volunteer", VALID_VOLUNTEER)
        html = client.get("/thanks").text
    assert "Upcoming events you could join" in html
    assert "Why we suggested this" not in html
    assert "/events/" in html


def test_thanks_page_falls_back_when_no_event_shares_an_interest(client, seeded):
    from app.models import Event

    for event in seeded.scalars(select(Event)):
        event.tags = "rajasthan"  # outside the interest vocabulary, so nothing can match
    seeded.commit()
    submit(client, "/volunteer", VALID_VOLUNTEER)
    html = client.get("/thanks").text
    assert "Upcoming events you could join" in html
    assert "Why we suggested this" not in html


def test_admin_rows_show_a_suggested_event(settings):
    password = "correct horse battery staple"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()
    app = create_app(settings.model_copy(update={"admin_password_hash": SecretStr(hashed)}))
    with TestClient(app) as client:
        from app.seed import seed

        with app.state.db.session() as s:
            seed(s)
        submit(client, "/volunteer", VALID_VOLUNTEER)
        page = client.get("/admin/login").text
        token = page.split('name="csrf_token" value="')[1].split('"')[0]
        client.post(
            "/admin/login", data={"csrf_token": token, "username": "admin", "password": password}
        )
        assert 'Suggested: <a href="/events/' in client.get("/admin").text


# --- Related posts ---------------------------------------------------------------


def test_post_pages_use_tfidf_related_posts(client, app, seeded):
    assert isinstance(app.state.related_posts, TfidfRelatedPosts)
    posts = seeded.scalars(select(Post)).all()
    with_related = 0
    for post in posts:
        html = client.get(f"/blog/{post.slug}").text
        assert f'href="/blog/{post.slug}"' not in html.split("You might also like")[-1]
        with_related += "You might also like" in html
    assert with_related == len(posts)  # every seeded post finds at least one neighbour


def test_related_posts_fall_back_to_tags_when_the_flag_is_off(settings):
    app = create_app(settings.model_copy(update={"ml_related_posts": False}))
    assert app.state.related_posts is posts_sharing_tags
