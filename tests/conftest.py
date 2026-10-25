"""Shared fixtures: every test gets its own app, SQLite file and outbox."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,  # never read the developer's .env during tests
        app_env="test",
        secret_key="test-secret-key-not-for-production",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        email_backend="memory",
        outbox_dir=tmp_path / "outbox",
        ml_spam_filter=False,
        spam_model_path=tmp_path / "missing-model.joblib",
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    # The context manager runs the lifespan, which creates the tables.
    with TestClient(app) as test_client:
        yield test_client
