"""Single source of truth for branding and runtime settings.

Two different kinds of configuration live here on purpose:

* ``BRAND`` is *identity*: name, tagline, colours, contact details. It is not secret and
  changes only when the site is rebranded, so it is plain Python you edit in one place.
* ``Settings`` is *environment*: secrets, database URL, email backend, feature flags.
  It is read from environment variables (or a local ``.env``) and never hardcoded.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PrivateAttr, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BrandColors:
    """Brand palette. Every pair used for text is checked for WCAG AA contrast in tests."""

    primary: str = "#0F5E5A"  # deep teal: headers, links, primary buttons
    primary_dark: str = "#0A4542"  # hover/active states, footer background
    primary_light: str = "#E3F0EE"  # tinted section backgrounds
    accent: str = "#E89B2D"  # saffron: reserved for the Donate CTA and highlights
    accent_dark: str = "#D08A1F"  # hover; still 5.2:1 against ink text
    background: str = "#FBF8F3"  # warm off-white page background
    surface: str = "#FFFFFF"  # cards and form fields
    ink: str = "#1F2933"  # body text
    muted: str = "#52606D"  # secondary text
    border: str = "#D9D3C7"
    success: str = "#1E6B3A"
    error: str = "#B42318"
    warning_bg: str = "#FFF4D6"  # demo-mode banner


@dataclass(frozen=True)
class Brand:
    name: str = "Akshar Foundation"
    short_name: str = "Akshar"
    tagline: str = "Every child, every letter, every village."
    mission: str = (
        "We help children in rural India read, write and reason with confidence by running "
        "free community learning centres, training local teachers and keeping girls in school."
    )
    description: str = (
        "Akshar Foundation runs free community learning centres for children aged 6 to 14 "
        "in rural Rajasthan and Jharkhand."
    )
    founded_year: int = 2014
    # Obviously fictional identifiers so nobody mistakes the demo for a real charity.
    registration: str = "Registered Trust No. DEMO/2014/0001 (fictional)"
    email: str = "hello@akshar.example.org"
    phone: str = "+91 00000 00000"
    address: str = "12 Demo Lane, Civil Lines, Jaipur, Rajasthan 302006 (fictional)"
    social: dict[str, str] = field(
        default_factory=lambda: {
            "Instagram": "https://instagram.com/example",
            "LinkedIn": "https://www.linkedin.com/company/example",
            "YouTube": "https://www.youtube.com/@example",
        }
    )
    colors: BrandColors = field(default_factory=BrandColors)
    currency: str = "INR"
    locale: str = "en-IN"


BRAND = Brand()


class Settings(BaseSettings):
    """Runtime settings. Each field maps to an upper-case environment variable."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["development", "test", "production"] = "development"
    # Optional only so local dev works out of the box; production refuses to start without it.
    secret_key: SecretStr | None = None
    site_url: str = "http://localhost:8000"
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'akshar.db'}"

    # Email: "outbox" writes .eml files you can open, "console" logs them, "smtp" sends.
    email_backend: Literal["console", "outbox", "smtp", "memory"] = "outbox"
    email_from: str = "Akshar Foundation <no-reply@akshar.example.org>"
    outbox_dir: Path = BASE_DIR / "outbox"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = True

    # Admin: one account, password stored only as a bcrypt hash.
    admin_username: str = "admin"
    admin_password_hash: SecretStr | None = None

    # Abuse protection. Counts every POST attempt to a public form, per client IP.
    rate_limit_max: int = Field(default=8, ge=1)
    rate_limit_window_seconds: int = Field(default=600, ge=1)
    # Only enable behind a proxy you control, otherwise clients can spoof their IP.
    trust_proxy_headers: bool = False

    # ML feature flags. Each feature has a non-ML fallback, so the site works with all off.
    ml_related_posts: bool = True
    ml_event_matching: bool = True
    ml_spam_filter: bool = True
    spam_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    spam_model_path: Path = BASE_DIR / "data" / "spam_model.joblib"

    _ephemeral_secret: str | None = PrivateAttr(default=None)

    @field_validator("outbox_dir", "spam_model_path")
    @classmethod
    def _resolve_relative_paths(cls, value: Path) -> Path:
        # Relative paths in .env are relative to the project root, not the current directory.
        return value if value.is_absolute() else BASE_DIR / value

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_path(cls, value: str) -> str:
        prefix = "sqlite:///"
        if value.startswith(prefix) and ":memory:" not in value:
            path = Path(value.removeprefix(prefix))
            if not path.is_absolute():
                return f"{prefix}{BASE_DIR / path}"
        return value

    @model_validator(mode="after")
    def _require_secret_in_production(self) -> Settings:
        if self.app_env == "production" and self.secret_key is None:
            raise ValueError("SECRET_KEY must be set when APP_ENV=production")
        if self.email_backend == "smtp" and not self.smtp_host:
            raise ValueError("SMTP_HOST must be set when EMAIL_BACKEND=smtp")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def resolved_secret_key(self) -> str:
        """Return the configured secret, or a per-process random one in dev/test.

        A random key means sessions reset on every restart, which is acceptable locally and
        far safer than shipping a default secret that someone forgets to change.
        """
        if self.secret_key is not None:
            return self.secret_key.get_secret_value()
        if self._ephemeral_secret is None:
            logger.warning("SECRET_KEY not set; using a random key for this process only.")
            self._ephemeral_secret = secrets.token_urlsafe(32)
        return self._ephemeral_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
