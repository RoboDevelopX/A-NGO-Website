"""Donate flow (mock payments only) and receipts."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app.content import DONATION_IMPACT, programme_share
from app.db import get_db
from app.models import Donation
from app.schemas import (
    CLIENT_MESSAGES,
    DONATION_MAX,
    DONATION_MIN,
    PRESET_AMOUNTS,
    DonationForm,
    friendly_errors,
)
from app.security import check_rate_limit, csrf_protected_form, honeypot_triggered, read_form_nonce
from app.services.donations import process_donation, receipt_email
from app.services.email import send_safely
from app.services.payments import DEMO_DECLINE_AMOUNT_PAISE, Frequency
from app.templating import render

logger = logging.getLogger(__name__)
router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
CSRFForm = Annotated[FormData, Depends(csrf_protected_form)]

FIELDS = ("frequency", "amount_choice", "custom_amount", "name", "email")
MAX_RECEIPTS_IN_SESSION = 10


def _context(values: dict, errors: dict | None = None, **extra) -> dict:
    return {
        "values": values,
        "errors": errors or {},
        "messages": CLIENT_MESSAGES,
        "presets": [(amount, DONATION_IMPACT.get(amount, "")) for amount in PRESET_AMOUNTS],
        "donation_min": DONATION_MIN,
        "donation_max": DONATION_MAX,
        "decline_amount": DEMO_DECLINE_AMOUNT_PAISE // 100,
        "programme_share": programme_share(),
        **extra,
    }


@router.get("/donate")
def donate_page(request: Request, amount: str | None = None, frequency: str | None = None):
    # Query parameters let other pages deep-link a preset, e.g. /donate?frequency=monthly.
    values = {
        "amount_choice": amount if amount in {str(a) for a in PRESET_AMOUNTS} else "1000",
        "frequency": frequency if frequency in {f.value for f in Frequency} else "one_time",
    }
    return render(request, "pages/donate.html", _context(values))


@router.post("/donate")
async def donate_submit(request: Request, form: CSRFForm, db: DB, background: BackgroundTasks):
    values = {key: form.get(key) if isinstance(form.get(key), str) else "" for key in FIELDS}

    if (retry_after := check_rate_limit(request)) is not None:
        return render(
            request,
            "pages/donate.html",
            _context(values, rate_limited=True),
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
    if honeypot_triggered(form):
        logger.info("Honeypot triggered on donate form")
        return RedirectResponse("/donate", status_code=303)
    nonce = read_form_nonce(form)
    if nonce is None:
        raise HTTPException(status_code=400, detail="Missing form token")

    try:
        data = DonationForm.model_validate(values)
    except ValidationError as exc:
        return render(
            request, "pages/donate.html", _context(values, friendly_errors(exc)), status_code=422
        )

    outcome = process_donation(db, request.app.state.payment_provider, data, nonce)
    donation = outcome.donation
    if donation.status != "succeeded":
        # 402 Payment Required: the request was fine, the (mock) bank said no.
        return render(
            request,
            "pages/donate.html",
            _context(values, declined_message=donation.failure_reason),
            status_code=402,
        )

    receipts = [r for r in request.session.get("receipts", []) if r != donation.receipt_no]
    request.session["receipts"] = [*receipts, donation.receipt_no][-MAX_RECEIPTS_IN_SESSION:]
    if not outcome.replayed:
        email = receipt_email(donation, request.app.state.settings.site_url)
        background.add_task(send_safely, request.app.state.email_service, email)
    return RedirectResponse(f"/donate/receipt/{donation.receipt_no}", status_code=303)


@router.get("/donate/receipt/{receipt_no}")
def receipt(request: Request, receipt_no: str, db: DB):
    # Receipts show a name and email, so only the browser session that made the donation
    # can view one. Anyone else gets the same 404 as a receipt that doesn't exist.
    if receipt_no not in request.session.get("receipts", []):
        raise HTTPException(status_code=404)
    donation = db.scalar(
        select(Donation).where(Donation.receipt_no == receipt_no, Donation.status == "succeeded")
    )
    if donation is None:
        raise HTTPException(status_code=404)
    return render(request, "pages/receipt.html", {"donation": donation, "noindex": True})
