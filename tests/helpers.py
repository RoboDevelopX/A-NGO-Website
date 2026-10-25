"""Test helpers for driving HTML forms through TestClient."""

from __future__ import annotations

import re

_CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
_NONCE_RE = re.compile(r'name="form_nonce" value="([^"]+)"')


def form_tokens(client, url: str) -> dict[str, str]:
    """GET a page and return the hidden security fields its form needs."""
    html = client.get(url).text
    return {
        "csrf_token": _CSRF_RE.search(html).group(1),
        "form_nonce": _NONCE_RE.search(html).group(1),
    }


VALID_VOLUNTEER = {
    "name": "Priya Sharma",
    "email": "priya.sharma@example.com",
    "phone": "+91 98765 43210",
    "interests": ["teaching", "library"],
    "availability": "weekends",
    "message": "I teach maths at a school in Jaipur and would love to help on Saturdays.",
}

VALID_CONTACT = {
    "name": "Rohan Gupta",
    "email": "rohan@example.com",
    "topic": "partnership",
    "message": "Our company would like to discuss a CSR partnership for 2027.",
}


def submit(client, url: str, data: dict, page: str | None = None, **overrides):
    """Fetch fresh tokens from ``page`` (default: ``url``), then POST without following
    the redirect."""
    payload = {**form_tokens(client, page or url), **data, **overrides}
    return client.post(url, data=payload, follow_redirects=False)
