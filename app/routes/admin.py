"""Password-protected admin: list, search and triage submissions, export CSV."""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app.db import get_db, utcnow
from app.models import Submission
from app.schemas import AVAILABILITY_LABELS, INTEREST_LABELS, TOPIC_LABELS
from app.security import check_rate_limit, csrf_protected_form, rotate_csrf_token
from app.services.admin import (
    KIND_FILTERS,
    SPAM_FILTERS,
    STATUS_FILTERS,
    SubmissionFilters,
    dashboard_stats,
    filtered_query,
    list_submissions,
    submissions_csv,
    verify_admin,
)
from app.templating import render

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")
DB = Annotated[Session, Depends(get_db)]
CSRFForm = Annotated[FormData, Depends(csrf_protected_form)]
PER_PAGE = 25
# Admin pages hold personal data: never cache them, never index them.
PRIVATE_HEADERS = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}


class AdminLoginRequired(Exception):
    pass


def require_admin(request: Request) -> str:
    username = request.session.get("admin")
    if not username:
        raise AdminLoginRequired()
    return username


Admin = Annotated[str, Depends(require_admin)]


def _render(request: Request, name: str, context: dict, status_code: int = 200):
    return render(request, name, {**context, "noindex": True}, status_code, headers=PRIVATE_HEADERS)


@router.get("/login")
def login_page(request: Request):
    if request.session.get("admin"):
        return RedirectResponse("/admin", status_code=303)
    enabled = request.app.state.settings.admin_password_hash is not None
    return _render(request, "admin/login.html", {"enabled": enabled, "error": None})


@router.post("/login")
async def login(request: Request, form: CSRFForm):
    settings = request.app.state.settings
    enabled = settings.admin_password_hash is not None
    username = form.get("username") if isinstance(form.get("username"), str) else ""
    password = form.get("password") if isinstance(form.get("password"), str) else ""

    # Separate, stricter bucket from public forms: this is the brute-force target.
    if check_rate_limit(request, scope="login") is not None:
        logger.warning("Admin login rate limit hit")
        context = {"enabled": enabled, "error": "Too many attempts. Please wait a few minutes."}
        return _render(request, "admin/login.html", context, 429)

    if not verify_admin(settings, username, password):
        logger.warning("Failed admin login for username %r", username[:40])
        context = {"enabled": enabled, "error": "Incorrect username or password."}
        return _render(request, "admin/login.html", context, 401)

    # Start a fresh session on login (no session fixation), with a new CSRF token.
    request.session.clear()
    request.session["admin"] = settings.admin_username
    rotate_csrf_token(request)
    logger.info("Admin logged in")
    return RedirectResponse("/admin", status_code=303)


@router.post("/logout")
async def logout(request: Request, form: CSRFForm):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


def _filters(request: Request) -> SubmissionFilters:
    p = request.query_params
    return SubmissionFilters.from_query(p.get("q"), p.get("status"), p.get("kind"), p.get("spam"))


@router.get("")
def dashboard(request: Request, db: DB, admin: Admin, page: str = "1"):
    filters = _filters(request)
    page_no = int(page) if page.isdigit() and int(page) > 0 else 1
    items, total = list_submissions(db, filters, page_no, PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    params = filters.as_params()

    def url_for_page(n: int) -> str:
        query = {**params, **({"page": n} if n > 1 else {})}
        return "/admin" + (f"?{urlencode(query)}" if query else "")

    return _render(
        request,
        "admin/dashboard.html",
        {
            "admin": admin,
            "items": items,
            "total": total,
            "page": page_no,
            "total_pages": total_pages,
            "url_for_page": url_for_page,
            "filters": filters,
            "export_url": "/admin/submissions.csv" + (f"?{urlencode(params)}" if params else ""),
            "return_to": url_for_page(page_no),
            "stats": dashboard_stats(db),
            "status_filters": STATUS_FILTERS,
            "kind_filters": KIND_FILTERS,
            "spam_filters": SPAM_FILTERS,
            "statuses": Submission.STATUSES,
            "interest_labels": {k.value: v[0] for k, v in INTEREST_LABELS.items()},
            "availability_labels": {k.value: v for k, v in AVAILABILITY_LABELS.items()},
            "topic_labels": {k.value: v for k, v in TOPIC_LABELS.items()},
            "suggestions": request.app.state.admin_suggestions(db, items),
        },
    )


@router.post("/submissions/{submission_id}/status")
async def update_status(request: Request, submission_id: int, form: CSRFForm, db: DB, admin: Admin):
    status = form.get("status")
    if status not in Submission.STATUSES:
        raise HTTPException(status_code=400)
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404)
    submission.status = status
    db.commit()
    logger.info("Submission %s marked %s by %s", submission_id, status, admin)
    return_to = form.get("return_to")
    # Only redirect within the admin, never to a URL supplied by the form (open redirect).
    target = (
        return_to if isinstance(return_to, str) and return_to.startswith("/admin") else "/admin"
    )
    if "//" in target or "\\" in target:
        target = "/admin"
    return RedirectResponse(target, status_code=303)


@router.get("/submissions.csv")
def export_csv(request: Request, db: DB, admin: Admin) -> Response:
    rows = db.scalars(filtered_query(_filters(request)))
    filename = f"submissions-{utcnow():%Y%m%d-%H%M}.csv"
    logger.info("Submissions exported by %s at %s", admin, datetime.now().isoformat())
    return Response(
        submissions_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={**PRIVATE_HEADERS, "Content-Disposition": f'attachment; filename="{filename}"'},
    )
