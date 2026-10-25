"""Stage (d): donate flow with the mock payment provider."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Donation
from app.services.payments import DEMO_DECLINE_AMOUNT_PAISE
from tests.helpers import form_tokens, submit

DONOR = {
    "frequency": "one_time",
    "amount_choice": "1000",
    "name": "Asha Nair",
    "email": "asha@example.com",
}


def donations(app) -> list[Donation]:
    with app.state.db.session() as s:
        return list(s.scalars(select(Donation)))


def test_donate_page_has_demo_banner_and_no_card_field_names(client):
    response = client.get("/donate")
    assert response.status_code == 200
    html = response.text
    assert "Demo mode, no real payment is processed" in html
    assert 'id="other-ways"' in html and "DEMO0000001" in html
    # The demo card inputs must never be submitted: no name attribute on them.
    card_inputs = re.findall(r'<input[^>]*id="demo-(?:card|expiry|cvc)"[^>]*>', html)
    assert len(card_inputs) == 3
    assert all("name=" not in tag and "readonly" in tag for tag in card_inputs)


def test_donate_page_preselects_from_query(client):
    html = client.get("/donate?frequency=monthly&amount=2500").text
    assert 'value="monthly" checked' in html
    assert 'value="2500" checked' in html


def test_successful_donation_records_redirects_and_emails(client, app):
    response = submit(client, "/donate", DONOR)
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/donate/receipt/AKF-")

    [donation] = donations(app)
    assert (donation.amount_paise, donation.status, donation.provider) == (
        100_000,
        "succeeded",
        "mock",
    )
    assert donation.frequency == "one_time"

    receipt = client.get(location)
    assert receipt.status_code == 200
    assert "Demo receipt" in receipt.text and "₹1,000" in receipt.text
    assert donation.receipt_no in receipt.text

    [mail] = app.state.email_service.sent
    assert mail.to == "asha@example.com" and "[DEMO]" in mail.subject
    assert donation.receipt_no in mail.body


def test_monthly_custom_amount(client, app):
    response = submit(
        client,
        "/donate",
        {**DONOR, "frequency": "monthly", "amount_choice": "custom", "custom_amount": "₹2,750"},
    )
    assert response.status_code == 303
    [donation] = donations(app)
    assert donation.amount_paise == 275_000
    assert donation.frequency == "monthly"
    assert donation.provider_ref.startswith("mock_sub_")
    assert "a month" in client.get(response.headers["location"]).text


def test_invalid_custom_amount_shows_error(client, app):
    response = submit(
        client, "/donate", {**DONOR, "amount_choice": "custom", "custom_amount": "50"}
    )
    assert response.status_code == 422
    assert "Enter a whole number of rupees between ₹100" in response.text
    assert donations(app) == []


def test_declined_payment_is_recorded_and_explained(client, app):
    amount = str(DEMO_DECLINE_AMOUNT_PAISE // 100)
    response = submit(
        client, "/donate", {**DONOR, "amount_choice": "custom", "custom_amount": amount}
    )
    assert response.status_code == 402
    assert "Payment declined" in response.text
    assert "Nothing has been charged" in response.text
    [donation] = donations(app)
    assert donation.status == "declined"
    assert app.state.email_service.sent == []


def test_double_submit_records_one_donation(client, app):
    payload = {**form_tokens(client, "/donate"), **DONOR}
    first = client.post("/donate", data=payload, follow_redirects=False)
    second = client.post("/donate", data=payload, follow_redirects=False)
    assert first.headers["location"] == second.headers["location"]
    assert len(donations(app)) == 1
    assert app.state.payment_provider.charges == 1
    assert len(app.state.email_service.sent) == 1


def test_receipt_is_private_to_the_donor_session(client, app):
    location = submit(client, "/donate", DONOR).headers["location"]
    with TestClient(app) as stranger:
        assert stranger.get(location).status_code == 404
    assert client.get("/donate/receipt/AKF-00000000-NOTREAL").status_code == 404


def test_donate_requires_csrf(client, app):
    response = client.post("/donate", data=DONOR)
    assert response.status_code == 403
    assert donations(app) == []


def test_no_card_data_reaches_the_database(client, app):
    # Even if a client sends card-like fields, nothing stores them.
    submit(client, "/donate", {**DONOR, "card_number": "4111111111111111", "cvc": "999"})
    columns = {c.name for c in Donation.__table__.columns}
    assert not columns & {"card_number", "cvc", "cvv", "expiry"}
    with app.state.db.engine.connect() as conn:
        dump = "\n".join(conn.connection.iterdump())
    assert "4111111111111111" not in dump
