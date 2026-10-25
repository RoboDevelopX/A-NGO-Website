"""Security helpers: response headers, CSRF, form nonces, rate limiting and the honeypot."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from starlette.datastructures import FormData, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Everything is served from our own origin: no CDNs, no inline scripts or styles.
# That lets the CSP stay strict, which is the single most effective XSS mitigation here.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "img-src 'self' data:",
        "style-src 'self'",
        "script-src 'self'",
        "font-src 'self'",
        "connect-src 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "object-src 'none'",
    ]
)


class SecureHeadersMiddleware:
    """Pure ASGI middleware (not BaseHTTPMiddleware) so it does not buffer responses."""

    def __init__(self, app: ASGIApp, *, hsts: bool = False) -> None:
        self.app = app
        self.headers = {
            "Content-Security-Policy": CONTENT_SECURITY_POLICY,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            "Cross-Origin-Opener-Policy": "same-origin",
        }
        if hsts:
            # Only over HTTPS in production; sending HSTS on localhost can break other dev sites.
            self.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in self.headers.items():
                    headers.setdefault(key, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
# Synchronizer-token pattern: a random token lives in the signed session cookie and is
# echoed in every form. A cross-site attacker can make the browser send the cookie but
# cannot read it to put the matching value in the form body. SameSite=Lax on the session
# cookie and an Origin check are extra layers, not the main defence.

CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
NONCE_FORM_FIELD = "form_nonce"
_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")


class CSRFError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="CSRF token missing or invalid")


def get_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


def rotate_csrf_token(request: Request) -> None:
    """Call on privilege changes (admin login) so a pre-login token can't be reused."""
    request.session[CSRF_SESSION_KEY] = secrets.token_urlsafe(32)


def _origin_matches(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin or origin == "null":
        return origin is None  # missing is fine (older browsers); literal "null" is not
    return urlsplit(origin).netloc == request.url.netloc


async def csrf_protected_form(request: Request) -> FormData:
    """FastAPI dependency for every HTML form POST: returns the parsed form or raises 403."""
    form = await request.form()
    sent = form.get(CSRF_FORM_FIELD)
    expected = request.session.get(CSRF_SESSION_KEY)
    if (
        not isinstance(sent, str)
        or not expected
        or not secrets.compare_digest(sent, expected)
        or not _origin_matches(request)
    ):
        raise CSRFError()
    return form


def new_form_nonce() -> str:
    return secrets.token_hex(16)


def read_form_nonce(form: FormData) -> str | None:
    nonce = form.get(NONCE_FORM_FIELD)
    return nonce if isinstance(nonce, str) and _NONCE_RE.match(nonce) else None


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class RateLimiter:
    """In-memory sliding-window limiter: at most ``max_hits`` per ``window`` seconds per key.

    Good enough for a single process. With several workers or servers each would keep its
    own counts, so production would move this to Redis (same interface, shared state).
    """

    def __init__(
        self, max_hits: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.max_hits = max_hits
        self.window = window_seconds
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, key: str) -> bool:
        """Record an attempt. Returns False (and records nothing) if the key is over limit."""
        now = self.clock()
        with self._lock:
            self._calls += 1
            if self._calls % 1000 == 0:
                self._prune(now)
            hits = self._hits[key]
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) >= self.max_hits:
                return False
            hits.append(now)
            return True

    def retry_after(self, key: str) -> int:
        with self._lock:
            hits = self._hits.get(key)
            if not hits:
                return 0
            return max(1, int(hits[0] + self.window - self.clock()) + 1)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _prune(self, now: float) -> None:
        stale = [k for k, v in self._hits.items() if not v or v[-1] <= now - self.window]
        for key in stale:
            del self._hits[key]


def client_ip(request: Request) -> str:
    settings = request.app.state.settings
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, scope: str = "form") -> int | None:
    """Count this attempt. Returns seconds to wait if over the limit, else None.

    Public forms share the "form" scope, so a bot can't get 8 tries per form.
    """
    limiter: RateLimiter = request.app.state.rate_limiter
    key = f"{scope}:{client_ip(request)}"
    if limiter.hit(key):
        return None
    return limiter.retry_after(key)


def hash_ip(ip: str, secret: str) -> str:
    return hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()[:32]


def honeypot_triggered(form: FormData) -> bool:
    value = form.get("website")
    return isinstance(value, str) and value.strip() != ""
