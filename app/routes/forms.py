"""Volunteer and contact forms: the fully functional part of the site.

Request pipeline for a POST (cheapest checks first):
  CSRF -> rate limit -> honeypot -> validation -> spam score -> save (+ nonce) -> email -> redirect
Every successful POST redirects to /thanks (Post/Redirect/GET), so refreshing the thank-you
page can never resubmit the form.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app.db import get_db
from app.models import Submission
from app.schemas import (
    AVAILABILITY_LABELS,
    CLIENT_MESSAGES,
    CONTACT_MESSAGE_MIN,
    INTEREST_LABELS,
    MESSAGE_MAX,
    TOPIC_LABELS,
    VOLUNTEER_MESSAGE_MIN,
    ContactForm,
    VolunteerForm,
    friendly_errors,
)
from app.security import (
    check_rate_limit,
    client_ip,
    csrf_protected_form,
    hash_ip,
    honeypot_triggered,
    read_form_nonce,
)
from app.services.content import upcoming_events
from app.services.email import send_safely
from app.services.submissions import (
    confirmation_email,
    first_name,
    form_values,
    save_submission,
)
from app.templating import render

logger = logging.getLogger(__name__)
router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
CSRFForm = Annotated[FormData, Depends(csrf_protected_form)]

FORMS = {
    "volunteer": {"schema": VolunteerForm, "template": "pages/volunteer.html"},
    "contact": {"schema": ContactForm, "template": "pages/contact.html"},
}


def _form_context(kind: str, values: dict | None = None, errors: dict | None = None) -> dict:
    return {
        "values": values or {"interests": []},
        "errors": errors or {},
        "messages": CLIENT_MESSAGES,
        "interest_options": [
            (i.value, label, hint) for i, (label, hint) in INTEREST_LABELS.items()
        ],
        "availability_options": [(a.value, label) for a, label in AVAILABILITY_LABELS.items()],
        "topic_options": [(t.value, label) for t, label in TOPIC_LABELS.items()],
        "message_min": VOLUNTEER_MESSAGE_MIN if kind == "volunteer" else CONTACT_MESSAGE_MIN,
        "message_max": MESSAGE_MAX,
    }


def _thanks_redirect(request: Request, kind: str, submission_id: int | None) -> RedirectResponse:
    request.session["thanks"] = {"kind": kind, "id": submission_id}
    return RedirectResponse("/thanks", status_code=303)


async def _handle_post(
    kind: str, request: Request, form: FormData, db: Session, background: BackgroundTasks
):
    config = FORMS[kind]
    values = form_values(form)

    if (retry_after := check_rate_limit(request)) is not None:
        logger.warning("Rate limit hit on %s form", kind)
        context = _form_context(kind, values)
        context["rate_limited"] = True
        return render(
            request,
            config["template"],
            context,
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )

    if honeypot_triggered(form):
        # Look exactly like success so bots learn nothing, but store and send nothing.
        logger.info("Honeypot triggered on %s form", kind)
        return _thanks_redirect(request, kind, None)

    nonce = read_form_nonce(form)
    if nonce is None:
        raise HTTPException(status_code=400, detail="Missing form token")

    try:
        data = config["schema"].model_validate(values)
    except ValidationError as exc:
        context = _form_context(kind, values, friendly_errors(exc))
        return render(request, config["template"], context, status_code=422)

    secret = request.app.state.settings.resolved_secret_key()
    submission = save_submission(
        db, data=data, nonce=nonce, ip_hash=hash_ip(client_ip(request), secret)
    )
    if submission is None:
        logger.info("Duplicate %s submission ignored", kind)
        return RedirectResponse("/thanks", status_code=303)

    if not submission.is_spam:
        email = confirmation_email(submission, request.app.state.settings.site_url)
        background.add_task(send_safely, request.app.state.email_service, email)
    return _thanks_redirect(request, kind, submission.id)


@router.get("/volunteer")
def volunteer_page(request: Request):
    return render(request, "pages/volunteer.html", _form_context("volunteer"))


@router.post("/volunteer")
async def volunteer_submit(request: Request, form: CSRFForm, db: DB, background: BackgroundTasks):
    return await _handle_post("volunteer", request, form, db, background)


@router.get("/contact")
def contact_page(request: Request):
    return render(request, "pages/contact.html", _form_context("contact"))


@router.post("/contact")
async def contact_submit(request: Request, form: CSRFForm, db: DB, background: BackgroundTasks):
    return await _handle_post("contact", request, form, db, background)


@router.get("/thanks")
def thanks(request: Request, db: DB):
    info = request.session.get("thanks") or {}
    kind = info.get("kind", "contact")
    submission = db.get(Submission, info["id"]) if info.get("id") else None
    return render(
        request,
        "pages/thanks.html",
        {
            "kind": kind,
            "first_name": first_name(submission.name) if submission else None,
            "suggested_events": upcoming_events(db, limit=3) if kind == "volunteer" else [],
            "noindex": True,
        },
    )
