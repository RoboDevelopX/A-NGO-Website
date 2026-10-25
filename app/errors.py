"""Branded error pages. HTML for humans; the status code is preserved for crawlers."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.templating import render

logger = logging.getLogger(__name__)

_MESSAGES = {
    400: ("Something was wrong with that request", "Please go back and try again."),
    403: (
        "That form has expired",
        "For your security, forms expire after a while. Please reload the page and try again.",
    ),
    404: ("We couldn't find that page", "It may have moved, or the link may be mistyped."),
    405: ("That action isn't allowed here", "Please go back and try again."),
    429: ("You're going a little fast", "Please wait a few minutes and try again."),
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        title, message = _MESSAGES.get(exc.status_code, ("Something went wrong", str(exc.detail)))
        template = "errors/404.html" if exc.status_code == 404 else "errors/error.html"
        return render(
            request,
            template,
            {"status_code": exc.status_code, "title": title, "message": message},
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def server_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return render(
            request,
            "errors/500.html",
            {"status_code": 500, "title": "Something went wrong on our side"},
            status_code=500,
        )
