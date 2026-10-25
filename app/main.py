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
from app.routes import pages, seo
from app.security import SecureHeadersMiddleware

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
    for router in (pages.router, seo.router):
        app.include_router(router)
    register_error_handlers(app)
    return app
