"""Persisting public form submissions and building their confirmation emails."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app.config import BRAND
from app.models import FormToken, Submission, join_tags
from app.schemas import (
    AVAILABILITY_LABELS,
    INTEREST_LABELS,
    TOPIC_LABELS,
    ContactForm,
    VolunteerForm,
)
from app.services.email import Email, render_email

TEXT_FIELDS = ("name", "email", "phone", "message", "availability", "topic")


def form_values(form: FormData) -> dict:
    """Plain dict of submitted values, used both for validation and to refill the form."""
    values: dict = {}
    for key in TEXT_FIELDS:
        raw = form.get(key)
        values[key] = raw if isinstance(raw, str) else ""
    values["interests"] = [v for v in form.getlist("interests") if isinstance(v, str)]
    return values


def save_submission(
    db: Session,
    *,
    data: VolunteerForm | ContactForm,
    nonce: str,
    ip_hash: str,
    spam_score: float | None = None,
    is_spam: bool = False,
) -> Submission | None:
    """Store the submission and its one-time nonce in a single transaction.

    Returns None if the nonce was already used (a double submit). Relying on the primary
    key constraint, rather than "check then insert", is what makes this race-free when
    two identical requests arrive at the same moment.
    """
    kind = "volunteer" if isinstance(data, VolunteerForm) else "contact"
    submission = Submission(
        kind=kind,
        name=data.name,
        email=data.email,
        phone=data.phone,
        message=data.message,
        interests=join_tags(data.interests) if isinstance(data, VolunteerForm) else "",
        availability=data.availability.value if isinstance(data, VolunteerForm) else None,
        topic=data.topic.value if isinstance(data, ContactForm) else None,
        ip_hash=ip_hash,
        spam_score=spam_score,
        is_spam=is_spam,
    )
    db.add(FormToken(token=nonce, kind=kind))
    db.add(submission)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    return submission


def first_name(name: str) -> str:
    return name.split(" ")[0]


def confirmation_email(submission: Submission, site_url: str) -> Email:
    common = {
        "first_name": first_name(submission.name),
        "brand_name": BRAND.name,
        "site_url": site_url,
    }
    if submission.kind == "volunteer":
        body = render_email(
            "volunteer_confirmation.txt",
            interest_labels=[INTEREST_LABELS[i][0] for i in submission.interest_list],
            availability_label=AVAILABILITY_LABELS[submission.availability],
            **common,
        )
        subject = f"Thanks for volunteering with {BRAND.name}"
    else:
        body = render_email(
            "contact_confirmation.txt", topic_label=TOPIC_LABELS[submission.topic], **common
        )
        subject = f"We've received your message - {BRAND.name}"
    return Email(to=submission.email, subject=subject, body=body)
