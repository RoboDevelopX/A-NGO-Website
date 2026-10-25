"""Content pages and the generated brand stylesheet."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from app.config import BRAND
from app.templating import render

router = APIRouter()


@router.get("/")
def home(request: Request):
    return render(request, "pages/home.html")


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
