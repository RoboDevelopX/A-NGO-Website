"""Donation flow: charge through a PaymentProvider and record the outcome."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import BRAND
from app.db import utcnow
from app.formatting import format_date, format_inr
from app.models import Donation
from app.schemas import DonationForm
from app.services.email import Email, render_email
from app.services.payments import PaymentProvider, PaymentRequest

# Crockford-style alphabet without look-alikes (0/O, 1/I/L) so receipts are easy to read out.
_RECEIPT_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def new_receipt_no() -> str:
    suffix = "".join(secrets.choice(_RECEIPT_ALPHABET) for _ in range(8))
    return f"AKF-{utcnow():%Y%m%d}-{suffix}"


@dataclass(frozen=True)
class DonationOutcome:
    donation: Donation
    replayed: bool  # True when this was a duplicate submit of an earlier donation


def find_by_idempotency_key(db: Session, key: str) -> Donation | None:
    return db.scalar(select(Donation).where(Donation.idempotency_key == key))


def process_donation(
    db: Session, provider: PaymentProvider, data: DonationForm, idempotency_key: str
) -> DonationOutcome:
    """Charge (mock) and record the donation, safely handling double submits."""
    if existing := find_by_idempotency_key(db, idempotency_key):
        return DonationOutcome(existing, replayed=True)

    amount_paise = data.amount_rupees * 100
    result = provider.charge(
        PaymentRequest(
            amount_paise=amount_paise,
            currency=BRAND.currency,
            frequency=data.frequency,
            donor_name=data.name,
            donor_email=data.email,
            idempotency_key=idempotency_key,
        )
    )
    donation = Donation(
        receipt_no=new_receipt_no(),
        amount_paise=amount_paise,
        currency=BRAND.currency,
        frequency=data.frequency.value,
        donor_name=data.name,
        donor_email=data.email,
        provider=provider.name,
        provider_ref=result.provider_ref,
        status=result.status.value,
        failure_reason=result.message if not result.succeeded else None,
        idempotency_key=idempotency_key,
    )
    db.add(donation)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent duplicate won the race. The provider's idempotency key guarantees
        # it was the same charge, so we return the stored row.
        db.rollback()
        existing = find_by_idempotency_key(db, idempotency_key)
        if existing is None:
            raise
        return DonationOutcome(existing, replayed=True)
    return DonationOutcome(donation, replayed=False)


def receipt_email(donation: Donation, site_url: str) -> Email:
    body = render_email(
        "donation_receipt.txt",
        first_name=donation.donor_name.split(" ")[0],
        brand_name=BRAND.name,
        registration=BRAND.registration,
        amount=format_inr(donation.amount_rupees),
        monthly=donation.frequency == "monthly",
        receipt_no=donation.receipt_no,
        date=format_date(donation.created_at),
        site_url=site_url,
    )
    return Email(
        to=donation.donor_email,
        subject=f"[DEMO] Your receipt {donation.receipt_no} from {BRAND.name}",
        body=body,
    )
