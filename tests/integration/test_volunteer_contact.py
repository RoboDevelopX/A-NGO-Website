"""Stage (c): the volunteer and contact forms end to end."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import FormToken, Submission
from tests.helpers import VALID_CONTACT, VALID_VOLUNTEER, form_tokens, submit


def count(app, model=Submission) -> int:
    with app.state.db.session() as s:
        return s.scalar(select(func.count()).select_from(model))


@pytest.mark.parametrize("path", ["/volunteer", "/contact"])
def test_form_pages_render_with_security_fields(client, path):
    response = client.get(path)
    assert response.status_code == 200
    html = response.text
    assert 'name="csrf_token"' in html
    assert 'name="form_nonce"' in html
    assert 'name="website"' in html  # honeypot
    assert "novalidate" in html and "data-validate" in html
    assert 'data-msg-required="Enter your full name"' in html


def test_valid_volunteer_submission_is_saved_emailed_and_redirected(client, app):
    response = submit(client, "/volunteer", VALID_VOLUNTEER)
    assert response.status_code == 303
    assert response.headers["location"] == "/thanks"

    with app.state.db.session() as s:
        sub = s.scalars(select(Submission)).one()
    assert (sub.kind, sub.name, sub.email) == (
        "volunteer",
        "Priya Sharma",
        "priya.sharma@example.com",
    )
    assert sub.interest_list == ["library", "teaching"]
    assert sub.status == "new" and sub.is_spam is False
    assert sub.ip_hash and "testclient" not in sub.ip_hash

    sent = app.state.email_service.sent
    assert len(sent) == 1 and sent[0].to == "priya.sharma@example.com"

    thanks = client.get("/thanks")
    assert "Thank you, Priya!" in thanks.text
    assert "noindex" in thanks.text


def test_thanks_page_suggests_upcoming_events_for_volunteers(client, seeded):
    submit(client, "/volunteer", VALID_VOLUNTEER)
    html = client.get("/thanks").text
    assert "Upcoming events you could join" in html or "Suggested events" in html
    assert "/events/" in html


def test_invalid_submission_shows_friendly_errors_and_keeps_values(client, app):
    response = submit(
        client,
        "/volunteer",
        {**VALID_VOLUNTEER, "email": "priya@", "interests": [], "message": "Hi"},
    )
    assert response.status_code == 422
    html = response.text
    assert "There are 3 problems with your form" in html
    assert "Enter an email address in the correct format" in html
    assert "Choose at least one way you&#39;d like to help" in html
    assert "Tell us a little more" in html
    assert 'value="Priya Sharma"' in html  # what they typed is kept
    assert 'aria-invalid="true"' in html
    assert count(app) == 0
    assert app.state.email_service.sent == []


def test_honeypot_pretends_success_but_stores_nothing(client, app):
    response = submit(client, "/volunteer", VALID_VOLUNTEER, website="http://cheap-seo.example")
    assert response.status_code == 303
    assert response.headers["location"] == "/thanks"
    assert count(app) == 0
    assert app.state.email_service.sent == []


def test_missing_csrf_token_is_rejected(client, app):
    tokens = form_tokens(client, "/volunteer")
    response = client.post(
        "/volunteer", data={**VALID_VOLUNTEER, "form_nonce": tokens["form_nonce"]}
    )
    assert response.status_code == 403
    assert "form has expired" in response.text
    assert count(app) == 0


def test_wrong_csrf_token_is_rejected(client, app):
    response = submit(client, "/volunteer", VALID_VOLUNTEER, csrf_token="forged-token")
    assert response.status_code == 403
    assert count(app) == 0


def test_token_from_another_session_is_rejected(app):
    with TestClient(app) as attacker, TestClient(app) as victim:
        attacker_token = form_tokens(attacker, "/volunteer")
        victim.get("/volunteer")  # victim has their own session
        response = victim.post("/volunteer", data={**VALID_VOLUNTEER, **attacker_token})
    assert response.status_code == 403


def test_cross_origin_post_is_rejected(client):
    response = client.post(
        "/volunteer",
        data={**form_tokens(client, "/volunteer"), **VALID_VOLUNTEER},
        headers={"Origin": "https://evil.example"},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_double_submit_with_same_nonce_creates_one_row(client, app):
    payload = {**form_tokens(client, "/volunteer"), **VALID_VOLUNTEER}
    first = client.post("/volunteer", data=payload, follow_redirects=False)
    second = client.post("/volunteer", data=payload, follow_redirects=False)
    assert first.status_code == second.status_code == 303
    assert count(app) == 1
    assert count(app, FormToken) == 1
    assert len(app.state.email_service.sent) == 1


def test_missing_form_nonce_is_a_bad_request(client, app):
    tokens = form_tokens(client, "/volunteer")
    response = client.post(
        "/volunteer", data={**VALID_VOLUNTEER, "csrf_token": tokens["csrf_token"]}
    )
    assert response.status_code == 400
    assert count(app) == 0


def test_rate_limit_blocks_after_max_attempts(settings):
    app = create_app(settings.model_copy(update={"rate_limit_max": 3}))
    with TestClient(app) as client:
        statuses = [submit(client, "/volunteer", VALID_VOLUNTEER).status_code for _ in range(4)]
        assert statuses == [303, 303, 303, 429]
        blocked = submit(client, "/contact", VALID_CONTACT)  # limit is shared across forms
        assert blocked.status_code == 429
        assert int(blocked.headers["retry-after"]) > 0
        assert "Too many attempts" in blocked.text
        assert "Rohan Gupta" in blocked.text  # their message is not lost
    assert count(app) == 3


def test_valid_contact_submission(client, app):
    response = submit(client, "/contact", VALID_CONTACT)
    assert response.status_code == 303
    with app.state.db.session() as s:
        sub = s.scalars(select(Submission)).one()
    assert (sub.kind, sub.topic, sub.interests) == ("contact", "partnership", "")
    assert "Partnerships and CSR" in app.state.email_service.sent[0].body
    assert "Message received" in client.get("/thanks").text


def test_contact_validation_errors(client):
    response = submit(client, "/contact", {**VALID_CONTACT, "topic": "", "name": ""})
    assert response.status_code == 422
    assert "Choose what your message is about" in response.text
    assert "Enter your full name" in response.text


def test_session_cookie_is_httponly_and_samesite(client):
    response = client.get("/volunteer")
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
