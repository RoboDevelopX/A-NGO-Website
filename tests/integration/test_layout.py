"""Stage (a): layout, design system, security headers and SEO plumbing."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_home_renders_layout(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert '<html lang="en-IN">' in html
    assert 'href="#main"' in html  # skip link
    assert '<main id="main"' in html
    assert 'property="og:title"' in html
    assert 'rel="canonical"' in html


@pytest.mark.parametrize("path", ["/", "/styleguide"])
def test_pages_send_security_headers(client, path):
    response = client.get(path)
    assert response.status_code == 200
    csp = response.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "unsafe-inline" not in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" not in response.headers  # only in production


def test_brand_css_comes_from_config(client):
    from app.config import BRAND

    response = client.get("/brand.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert BRAND.colors.primary in response.text


def test_styleguide_is_not_indexed(client):
    assert '<meta name="robots" content="noindex' in client.get("/styleguide").text


def test_404_page_is_branded(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "find that page" in response.text
    assert "noindex" in response.text


def test_500_page_is_branded(app):
    def boom():
        raise RuntimeError("kaboom")

    app.add_api_route("/boom", boom)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")
    assert response.status_code == 500
    assert "Something went wrong" in response.text
    assert "kaboom" not in response.text  # no stack traces leak to visitors


def test_robots_and_sitemap(client):
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /admin" in robots.text
    assert "Sitemap: http://localhost:8000/sitemap.xml" in robots.text

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert sitemap.headers["content-type"].startswith("application/xml")
    assert "<loc>http://localhost:8000/about</loc>" in sitemap.text


def test_static_assets_served(client):
    assert client.get("/static/css/main.css").status_code == 200
    assert client.get("/static/js/main.js").status_code == 200
