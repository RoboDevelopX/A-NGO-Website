"""robots.txt and sitemap.xml."""

from __future__ import annotations

from xml.sax.saxutils import escape

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select

from app.models import Event, Post

router = APIRouter()

STATIC_PATHS = ["/", "/about", "/donate", "/volunteer", "/contact", "/events", "/blog"]


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request) -> str:
    site = request.app.state.settings.site_url.rstrip("/")
    lines = ["User-agent: *", "Disallow: /admin", "Disallow: /donate/receipt/", ""]
    return "\n".join([*lines, f"Sitemap: {site}/sitemap.xml", ""])


def sitemap_entries(request: Request) -> list[tuple[str, str | None]]:
    """(path, lastmod) pairs for every public, indexable page."""
    entries: list[tuple[str, str | None]] = [(path, None) for path in STATIC_PATHS]
    with request.app.state.db.session() as db:
        for slug, published in db.execute(select(Post.slug, Post.published_at)):
            entries.append((f"/blog/{slug}", published.date().isoformat()))
        for slug, created in db.execute(select(Event.slug, Event.created_at)):
            entries.append((f"/events/{slug}", created.date().isoformat()))
    return entries


@router.get("/sitemap.xml")
def sitemap(request: Request) -> Response:
    site = request.app.state.settings.site_url.rstrip("/")
    urls = []
    for path, lastmod in sitemap_entries(request):
        entry = f"<url><loc>{escape(site + path)}</loc>"
        if lastmod:
            entry += f"<lastmod>{lastmod}</lastmod>"
        urls.append(entry + "</url>")
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(urls) + "</urlset>"
    )
    return Response(body, media_type="application/xml")
