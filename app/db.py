"""Database engine and session handling.

The engine is created per application instance (see ``create_app``) instead of at import
time, so each test can point the app at its own throwaway SQLite file.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp. SQLite has no timezone type, so we store UTC and convert on display."""
    return datetime.now(UTC).replace(tzinfo=None)


class Database:
    def __init__(self, url: str) -> None:
        connect_args: dict = {}
        if url.startswith("sqlite"):
            # FastAPI runs sync routes in a threadpool; each request still gets its own session.
            connect_args["check_same_thread"] = False
            _ensure_sqlite_dir(url)
        self.engine: Engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(self.engine, "connect", _sqlite_pragmas)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    def create_all(self) -> None:
        # Importing models registers them on Base.metadata.
        from app import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def session(self) -> Session:
        return self.SessionLocal()


def _ensure_sqlite_dir(url: str) -> None:
    path = url.removeprefix("sqlite:///")
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def _sqlite_pragmas(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL lets the admin read while a visitor writes, without "database is locked" errors.
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_db(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    session = request.app.state.db.session()
    try:
        yield session
    finally:
        session.close()
