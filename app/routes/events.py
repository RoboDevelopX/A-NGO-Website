"""Events: listing with an upcoming/past filter, detail pages, RSVP and calendar export."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app.config import BRAND
from app.db import get_db
from app.formatting import format_datetime
from app.models import Event, EventRSVP, FormToken
from app.schemas import CLIENT_MESSAGES, FIELD_MESSAGES, MAX_GUESTS, RSVPForm, friendly_errors
from app.security import check_rate_limit, csrf_protected_form, honeypot_triggered, read_form_nonce
from app.services.calendar import event_to_ics
from app.services.content import get_event, past_events, upcoming_events
from app.services.email import Email, render_email, send_safely
from app.services.markdown import render_markdown
from app.templating import render

logger = logging.getLogger(__name__)
router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
CSRFForm = Annotated[FormData, Depends(csrf_protected_form)]


@router.get("/events")
def events_list(request: Request, db: DB, when: str = "upcoming"):
    when = "past" if when == "past" else "upcoming"
    events = past_events(db) if when == "past" else upcoming_events(db)
    return render(request, "pages/events.html", {"events": events, "when": when})


def _detail_context(request: Request, event: Event, values=None, errors=None, **extra) -> dict:
    site = request.app.state.settings.site_url.rstrip("/")
    flash = request.session.pop("flash", None)
    return {
        "event": event,
        "body_html": render_markdown(event.body),
        "is_past": event.is_past(),
        "is_full": event.seats_left == 0,
        "values": values or {},
        "errors": errors or {},
        "messages": {**CLIENT_MESSAGES, "guests": {"invalid": FIELD_MESSAGES["guests"]}},
        "max_guests": MAX_GUESTS,
        "flash": flash if flash and flash.get("slug") == event.slug else None,
        "absolute_url": f"{site}/events/{event.slug}",
        **extra,
    }


@router.get("/events/{slug}")
def event_detail(request: Request, slug: str, db: DB):
    event = get_event(db, slug)
    if event is None:
        raise HTTPException(status_code=404)
    return render(request, "pages/event_detail.html", _detail_context(request, event))


@router.get("/events/{slug}/calendar.ics")
def event_calendar(request: Request, slug: str, db: DB) -> Response:
    event = get_event(db, slug)
    if event is None:
        raise HTTPException(status_code=404)
    url = f"{request.app.state.settings.site_url.rstrip('/')}/events/{slug}"
    return Response(
        event_to_ics(event, url),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{slug}.ics"'},
    )


@router.post("/events/{slug}/rsvp")
async def event_rsvp(
    request: Request, slug: str, form: CSRFForm, db: DB, background: BackgroundTasks
):
    event = get_event(db, slug)
    if event is None:
        raise HTTPException(status_code=404)
    values = {
        k: form.get(k) if isinstance(form.get(k), str) else "" for k in ("name", "email", "guests")
    }
    template = "pages/event_detail.html"

    if (retry_after := check_rate_limit(request)) is not None:
        ctx = _detail_context(request, event, values, rate_limited=True)
        return render(request, template, ctx, 429, headers={"Retry-After": str(retry_after)})
    if honeypot_triggered(form):
        logger.info("Honeypot triggered on RSVP form")
        return RedirectResponse(f"/events/{slug}", status_code=303)
    nonce = read_form_nonce(form)
    if nonce is None:
        raise HTTPException(status_code=400, detail="Missing form token")
    if event.is_past():
        ctx = _detail_context(request, event, values, rsvp_error="This event has already happened.")
        return render(request, template, ctx, 409)

    try:
        data = RSVPForm.model_validate(values)
    except ValidationError as exc:
        ctx = _detail_context(request, event, values, friendly_errors(exc))
        return render(request, template, ctx, 422)

    if event.seats_left is not None and 1 + data.guests > event.seats_left:
        message = (
            "Sorry, this event is now fully booked."
            if event.seats_left == 0
            else f"Only {event.seats_left} place(s) left. Please reduce the number of guests."
        )
        return render(
            request, template, _detail_context(request, event, values, rsvp_error=message), 409
        )

    db.add(FormToken(token=nonce, kind="rsvp"))
    db.add(EventRSVP(event_id=event.id, name=data.name, email=data.email, guests=data.guests))
    try:
        db.commit()
    except IntegrityError:
        # Either a double submit (same nonce) or this email already RSVP'd. Both are fine.
        db.rollback()
        request.session["flash"] = {
            "slug": slug,
            "message": "You're already on the list for this event. See you there!",
        }
        return RedirectResponse(f"/events/{slug}#rsvp", status_code=303)

    request.session["flash"] = {
        "slug": slug,
        "message": f"You're on the list, {data.name.split(' ')[0]}! We've emailed you the details.",
    }
    site = request.app.state.settings.site_url.rstrip("/")
    body = render_email(
        "rsvp_confirmation.txt",
        first_name=data.name.split(" ")[0],
        event=event,
        guests=data.guests,
        when=format_datetime(event.starts_at),
        calendar_url=f"{site}/events/{slug}/calendar.ics",
        brand_name=BRAND.name,
    )
    email = Email(to=data.email, subject=f"You're registered: {event.title}", body=body)
    background.add_task(send_safely, request.app.state.email_service, email)
    return RedirectResponse(f"/events/{slug}#rsvp", status_code=303)
