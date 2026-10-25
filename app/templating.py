"""Jinja2 environment: one place for template globals and filters."""

from __future__ import annotations

from datetime import datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR, BRAND
from app.formatting import (
    format_compact_number,
    format_date,
    format_datetime,
    format_inr,
    reading_time_minutes,
    to_ist,
)

# (label, path). Donate is rendered separately as the primary CTA.
NAV_ITEMS: list[tuple[str, str]] = [
    ("About", "/about"),
    ("Events", "/events"),
    ("Blog", "/blog"),
    ("Volunteer", "/volunteer"),
    ("Contact", "/contact"),
]


def _common_context(request: Request) -> dict:
    settings = request.app.state.settings
    path = request.url.path
    return {
        "brand": BRAND,
        "nav_items": NAV_ITEMS,
        "current_path": path,
        "site_url": settings.site_url.rstrip("/"),
        "canonical_url": settings.site_url.rstrip("/") + path,
        "current_year": datetime.now().year,
    }


def _is_active(current_path: str, href: str) -> bool:
    return current_path == href or current_path.startswith(href + "/")


templates = Jinja2Templates(directory=BASE_DIR / "templates", context_processors=[_common_context])
env = templates.env
env.trim_blocks = True
env.lstrip_blocks = True
env.filters["inr"] = format_inr
env.filters["compact"] = format_compact_number
env.filters["date"] = format_date
env.filters["datetime"] = format_datetime
env.filters["reading_time"] = reading_time_minutes
env.filters["ist"] = to_ist
env.globals["is_active"] = _is_active


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200, **kw):
    """Thin wrapper so routes read as ``return render(request, "pages/home.html", {...})``."""
    return templates.TemplateResponse(request, name, context or {}, status_code=status_code, **kw)
