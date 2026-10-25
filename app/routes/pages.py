"""Content pages and the generated brand stylesheet."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app import content
from app.config import BRAND
from app.db import get_db
from app.services.content import latest_posts, upcoming_events
from app.templating import render

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]


@router.get("/")
def home(request: Request, db: DB):
    return render(
        request,
        "pages/home.html",
        {
            "hero_image": content.HERO_IMAGE,
            "stats": content.IMPACT_STATS,
            "programmes": content.PROGRAMMES,
            "gallery": content.GALLERY,
            "testimonials": content.TESTIMONIALS,
            "donation_impact": content.DONATION_IMPACT,
            "events": upcoming_events(db, limit=3),
            "posts": latest_posts(db, limit=3),
        },
    )


@router.get("/about")
def about(request: Request):
    return render(
        request,
        "pages/about.html",
        {
            "values": content.VALUES,
            "problem_points": content.PROBLEM_POINTS,
            "approach_steps": content.APPROACH_STEPS,
            "milestones": content.MILESTONES,
            "team": content.TEAM,
            "funds": content.FUNDS_BREAKDOWN,
            "stats": content.IMPACT_STATS,
        },
    )


@router.get("/styleguide")
def styleguide(request: Request):
    """Living style guide for the design system. Not linked in the nav and not indexed."""
    return render(request, "pages/styleguide.html")


@router.get("/brand.css")
def brand_css() -> Response:
    """Brand colours as CSS custom properties, generated from ``BRAND``.

    Serving this as a stylesheet (instead of an inline <style>) keeps the CSP free of
    'unsafe-inline' while still letting a rebrand happen in config.py alone.
    """
    c = BRAND.colors
    css = (
        ":root{"
        f"--color-primary:{c.primary};--color-primary-dark:{c.primary_dark};"
        f"--color-primary-light:{c.primary_light};--color-accent:{c.accent};"
        f"--color-accent-dark:{c.accent_dark};--color-bg:{c.background};"
        f"--color-surface:{c.surface};--color-ink:{c.ink};--color-muted:{c.muted};"
        f"--color-border:{c.border};--color-success:{c.success};--color-error:{c.error};"
        f"--color-warning-bg:{c.warning_bg};"
        "}"
    )
    return Response(css, media_type="text/css", headers={"Cache-Control": "public, max-age=300"})


@router.get("/healthz", include_in_schema=False)
def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")
