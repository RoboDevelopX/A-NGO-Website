"""Application factory.

Run with ``uvicorn --factory app.main:create_app``. A factory (rather than a module-level
``app``) means importing this module has no side effects, and tests can build an app with
their own settings and database.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, BRAND, Settings, get_settings
from app.db import Database
from app.errors import register_error_handlers
from app.routes import admin, blog, donate, events, forms, pages, seo
from app.security import RateLimiter, SecureHeadersMiddleware
from app.services.content import posts_sharing_tags
from app.services.email import build_email_service
from app.services.ml import TfidfRelatedPosts, admin_suggestions, build_spam_filter
from app.services.payments import MockPaymentProvider

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.db.create_all()
        yield
        app.state.db.engine.dispose()

    # This is a server-rendered site, not a public API, so the OpenAPI docs are switched off.
    app = FastAPI(
        title=BRAND.name, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.settings = settings
    app.state.db = Database(settings.database_url)
    app.state.email_service = build_email_service(settings)
    # The only provider that exists. Swapping in a real one is a change to this line.
    app.state.payment_provider = MockPaymentProvider()
    # ML features, each behind a flag with a plain fallback (see app/services/ml.py).
    app.state.related_posts = (
        TfidfRelatedPosts() if settings.ml_related_posts else posts_sharing_tags
    )
    app.state.admin_suggestions = (
        admin_suggestions if settings.ml_event_matching else (lambda db, items: {})
    )
    app.state.spam_filter = build_spam_filter(settings)
    app.state.rate_limiter = RateLimiter(
        settings.rate_limit_max, settings.rate_limit_window_seconds
    )

    # Starlette sessions are signed (not encrypted) cookies; we only store ids and tokens in them.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.resolved_secret_key(),
        session_cookie="akshar_session",
        max_age=60 * 60 * 8,
        same_site="lax",
        https_only=settings.is_production,
    )
    # Added last so it is the outermost middleware and decorates every response.
    app.add_middleware(SecureHeadersMiddleware, hsts=settings.is_production)

    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    for router in (
        pages.router,
        forms.router,
        donate.router,
        events.router,
        blog.router,
        seo.router,
        admin.router,
    ):
        app.include_router(router)
    register_error_handlers(app)
    return app
