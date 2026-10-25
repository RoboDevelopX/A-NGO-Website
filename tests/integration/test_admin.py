"""Stage (f): password-protected admin."""

from __future__ import annotations

import csv
import io

import bcrypt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.main import create_app
from app.models import Submission
from app.services.admin import csv_safe
from tests.helpers import VALID_CONTACT, VALID_VOLUNTEER, submit

PASSWORD = "correct horse battery staple"


@pytest.fixture
def admin_app(settings):
    # Low bcrypt cost keeps the tests fast; production hashes use the default cost (12).
    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    return create_app(settings.model_copy(update={"admin_password_hash": SecretStr(hashed)}))


@pytest.fixture
def admin_client(admin_app):
    with TestClient(admin_app) as client:
        yield client


def login(client, username="admin", password=PASSWORD):
    page = client.get("/admin/login").text
    token = page.split('name="csrf_token" value="')[1].split('"')[0]
    return client.post(
        "/admin/login",
        data={"csrf_token": token, "username": username, "password": password},
        follow_redirects=False,
    )


def csrf_from(html: str) -> str:
    return html.split('name="csrf_token" value="')[1].split('"')[0]


def add_submission(app, **fields) -> int:
    defaults = dict(
        kind="volunteer",
        name="Priya Sharma",
        email="priya@example.com",
        message="Happy to help on weekends",
        interests="teaching",
        availability="weekends",
    )
    with app.state.db.session() as s:
        sub = Submission(**{**defaults, **fields})
        s.add(sub)
        s.commit()
        return sub.id


@pytest.mark.parametrize("path", ["/admin", "/admin/submissions.csv"])
def test_admin_requires_login(admin_client, path):
    response = admin_client.get(path, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_login_page_is_private(admin_client):
    response = admin_client.get("/admin/login")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "noindex" in response.text


def test_wrong_password_and_wrong_username_are_rejected_the_same_way(admin_client):
    wrong_pw = login(admin_client, password="nope")
    wrong_user = login(admin_client, username="root")
    assert wrong_pw.status_code == wrong_user.status_code == 401
    assert "Incorrect username or password" in wrong_pw.text
    assert admin_client.get("/admin", follow_redirects=False).status_code == 303


def test_login_without_csrf_is_rejected(admin_client):
    response = admin_client.post("/admin/login", data={"username": "admin", "password": PASSWORD})
    assert response.status_code == 403


def test_login_is_disabled_without_a_password_hash(client):
    assert "Admin login is turned off" in client.get("/admin/login").text
    assert login(client).status_code == 401


def test_login_is_rate_limited(settings):
    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    app = create_app(
        settings.model_copy(update={"admin_password_hash": SecretStr(hashed), "rate_limit_max": 2})
    )
    with TestClient(app) as client:
        assert [login(client, password="x").status_code for _ in range(3)] == [401, 401, 429]
        assert login(client).status_code == 429  # even the right password must wait


def test_successful_login_shows_submissions(admin_client, admin_app):
    submit(admin_client, "/volunteer", VALID_VOLUNTEER)
    submit(admin_client, "/contact", VALID_CONTACT)
    response = login(admin_client)
    assert response.status_code == 303 and response.headers["location"] == "/admin"
    page = admin_client.get("/admin")
    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-store"
    assert "Priya Sharma" in page.text and "Rohan Gupta" in page.text
    assert "2 submissions" in page.text
    assert "Teaching and tutoring" in page.text


def test_search_and_filters(admin_client, admin_app):
    add_submission(admin_app, name="Asha Nair", email="asha@example.com", message="Coding club")
    add_submission(
        admin_app,
        name="Vikram Rao",
        email="vik@example.com",
        kind="contact",
        topic="media",
        interests="",
        availability=None,
        status="contacted",
    )
    add_submission(
        admin_app, name="Spam Bot", email="bot@example.com", is_spam=True, spam_score=0.97
    )
    login(admin_client)

    def names(query: str) -> set[str]:
        html = admin_client.get("/admin" + query).text
        return {n for n in ("Asha Nair", "Vikram Rao", "Spam Bot") if n in html}

    assert names("") == {"Asha Nair", "Vikram Rao"}  # spam hidden by default
    assert names("?q=coding") == {"Asha Nair"}
    assert names("?q=VIK%40example") == {"Vikram Rao"}  # case-insensitive, matches email
    assert names("?status=contacted") == {"Vikram Rao"}
    assert names("?kind=volunteer") == {"Asha Nair"}
    assert names("?spam=only") == {"Spam Bot"}
    assert names("?q=%25") == set()  # LIKE wildcards are escaped, not "match everything"


def test_status_update(admin_client, admin_app):
    sub_id = add_submission(admin_app)
    login(admin_client)
    token = csrf_from(admin_client.get("/admin").text)
    response = admin_client.post(
        f"/admin/submissions/{sub_id}/status",
        data={"csrf_token": token, "status": "contacted", "return_to": "/admin?status=new"},
        follow_redirects=False,
    )
    assert response.status_code == 303 and response.headers["location"] == "/admin?status=new"
    with admin_app.state.db.session() as s:
        assert s.get(Submission, sub_id).status == "contacted"


@pytest.mark.parametrize(
    "return_to", ["https://evil.example", "//evil.example", "/admin//evil.example"]
)
def test_status_update_does_not_open_redirect(admin_client, admin_app, return_to):
    sub_id = add_submission(admin_app)
    login(admin_client)
    token = csrf_from(admin_client.get("/admin").text)
    response = admin_client.post(
        f"/admin/submissions/{sub_id}/status",
        data={"csrf_token": token, "status": "archived", "return_to": return_to},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin"


def test_status_update_rejects_bad_values_and_csrf(admin_client, admin_app):
    sub_id = add_submission(admin_app)
    login(admin_client)
    token = csrf_from(admin_client.get("/admin").text)
    bad = admin_client.post(
        f"/admin/submissions/{sub_id}/status", data={"csrf_token": token, "status": "deleted"}
    )
    assert bad.status_code == 400
    no_csrf = admin_client.post(f"/admin/submissions/{sub_id}/status", data={"status": "archived"})
    assert no_csrf.status_code == 403
    missing = admin_client.post(
        "/admin/submissions/9999/status", data={"csrf_token": token, "status": "archived"}
    )
    assert missing.status_code == 404


def test_csv_export_respects_filters_and_neutralises_formulas(admin_client, admin_app):
    add_submission(admin_app, name="Asha Nair", message='=HYPERLINK("http://evil","click")')
    add_submission(admin_app, name="Vikram Rao", kind="contact", topic="media", interests="")
    login(admin_client)
    response = admin_client.get("/admin/submissions.csv?kind=volunteer")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(response.text.lstrip("﻿"))))
    assert [r["name"] for r in rows] == ["Asha Nair"]
    assert rows[0]["message"].startswith("'=HYPERLINK")


def test_html_in_submissions_is_escaped_in_admin(admin_client, admin_app):
    add_submission(admin_app, message="<script>alert('xss')</script> I can teach")
    login(admin_client)
    html = admin_client.get("/admin").text
    assert "<script>alert(" not in html
    assert "&lt;script&gt;" in html


def test_logout_clears_session(admin_client):
    login(admin_client)
    token = csrf_from(admin_client.get("/admin").text)
    assert (
        admin_client.post(
            "/admin/logout", data={"csrf_token": token}, follow_redirects=False
        ).status_code
        == 303
    )
    assert admin_client.get("/admin", follow_redirects=False).status_code == 303


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("=1+1", "'=1+1"),
        ("+91 98765", "'+91 98765"),
        ("-2", "'-2"),
        ("@SUM(A1)", "'@SUM(A1)"),
        ("Priya", "Priya"),
        (None, ""),
        (0.5, "0.5"),
    ],
)
def test_csv_safe(value, expected):
    assert csv_safe(value) == expected


def test_saved_submissions_have_expected_shape(admin_client, admin_app):
    submit(admin_client, "/volunteer", VALID_VOLUNTEER)
    with admin_app.state.db.session() as s:
        assert s.scalars(select(Submission)).one().status == "new"
