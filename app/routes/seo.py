"""robots.txt and sitemap.xml."""

from __future__ import annotations

from xml.sax.saxutils import escape

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

router = APIRouter()

STATIC_PATHS = ["/", "/about", "/donate", "/volunteer", "/contact", "/events", "/blog"]


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request) -> str:
    site = request.app.state.settings.site_url.rstrip("/")
    lines = ["User-agent: *", "Disallow: /admin", "Disallow: /donate/receipt/", ""]
    return "\n".join([*lines, f"Sitemap: {site}/sitemap.xml", ""])


def sitemap_entries(request: Request) -> list[tuple[str, str | None]]:
    """(path, lastmod) pairs. Dynamic pages are appended by later stages."""
    return [(path, None) for path in STATIC_PATHS]


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
