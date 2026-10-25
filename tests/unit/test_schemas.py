import pytest
from pydantic import ValidationError

from app.schemas import (
    FIELD_MESSAGES,
    Availability,
    ContactForm,
    Interest,
    VolunteerForm,
    clean_text,
    friendly_errors,
)
from tests.helpers import VALID_CONTACT, VALID_VOLUNTEER


def errors_for(model, **overrides) -> dict[str, str]:
    data = {**(VALID_VOLUNTEER if model is VolunteerForm else VALID_CONTACT), **overrides}
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate(data)
    return friendly_errors(exc_info.value)


def test_valid_volunteer_is_normalised():
    form = VolunteerForm.model_validate(
        {**VALID_VOLUNTEER, "name": "  Priya   Sharma ", "email": "Priya.Sharma@EXAMPLE.com"}
    )
    assert form.name == "Priya Sharma"
    assert form.email == "Priya.Sharma@example.com"  # domain lower-cased, local part kept
    assert form.interests == [Interest.TEACHING, Interest.LIBRARY]
    assert form.availability is Availability.WEEKENDS


def test_empty_form_gives_one_friendly_message_per_field():
    with pytest.raises(ValidationError) as exc_info:
        VolunteerForm.model_validate({})
    errors = friendly_errors(exc_info.value)
    assert set(errors) == {"name", "email", "message", "interests", "availability"}
    assert errors["interests"] == FIELD_MESSAGES["interests"]
    assert all("String should" not in msg for msg in errors.values())


@pytest.mark.parametrize("name", ["प्रिया शर्मा", "Mary-Jane O’Brien", "A. R. Rahman", "Zoë"])
def test_names_from_any_script_are_accepted(name):
    assert VolunteerForm.model_validate({**VALID_VOLUNTEER, "name": name}).name == name


@pytest.mark.parametrize("name", ["P", "R2D2", "<script>", "Robert'); DROP TABLE", "x" * 81])
def test_invalid_names_are_rejected(name):
    assert "name" in errors_for(VolunteerForm, name=name)


@pytest.mark.parametrize("email", ["", "priya", "priya@", "@example.com", "a b@example.com"])
def test_invalid_emails(email):
    assert "email" in errors_for(VolunteerForm, email=email)


@pytest.mark.parametrize("phone", ["", None, "98765 43210", "+91-98765-43210", "(011) 2345 6789"])
def test_phone_is_optional_and_flexible(phone):
    form = VolunteerForm.model_validate({**VALID_VOLUNTEER, "phone": phone})
    assert form.phone == (phone or None)


@pytest.mark.parametrize("phone", ["12345", "call me maybe", "+91 98765 43210 12345 6789"])
def test_invalid_phones(phone):
    assert "7 to 15 digits" in errors_for(VolunteerForm, phone=phone)["phone"]


def test_message_length_limits():
    assert "at least 20" in errors_for(VolunteerForm, message="Too short")["message"]
    assert "under 2000" in errors_for(VolunteerForm, message="x" * 2001)["message"]
    # The contact form allows a shorter message.
    assert ContactForm.model_validate({**VALID_CONTACT, "message": "Ten chars!"})


def test_interests_are_deduplicated_and_checked():
    form = VolunteerForm.model_validate({**VALID_VOLUNTEER, "interests": ["teaching", "teaching"]})
    assert form.interests == [Interest.TEACHING]
    assert "interests" in errors_for(VolunteerForm, interests=["hacking"])
    assert "interests" in errors_for(VolunteerForm, interests=[])


def test_contact_topic_must_be_a_known_choice():
    assert errors_for(ContactForm, topic="bitcoin") == {"topic": FIELD_MESSAGES["topic"]}


def test_clean_text_strips_control_characters_but_keeps_line_breaks():
    assert clean_text("Hi\x00 there\u200b\t!") == "Hi there !"  # zero-width space removed
    assert (
        clean_text("Line one\r\n\r\n\r\n\r\nLine two\x07", multiline=True) == "Line one\n\nLine two"
    )


def test_markup_is_stored_verbatim_and_escaped_on_output():
    # We don't mangle input; Jinja autoescaping protects every page that displays it.
    form = VolunteerForm.model_validate(
        {**VALID_VOLUNTEER, "message": "<script>alert(1)</script> I can teach on Sundays."}
    )
    assert form.message.startswith("<script>")


# --- Donations ------------------------------------------------------------------

from app.schemas import DonationForm  # noqa: E402

DONOR = {
    "frequency": "one_time",
    "amount_choice": "1000",
    "name": "Asha Nair",
    "email": "a@example.com",
}


@pytest.mark.parametrize(
    ("choice", "custom", "expected"),
    [
        ("500", "", 500),
        ("5000", "999", 5000),
        ("custom", "2500", 2500),
        ("custom", "₹1,00,000", 100000),
    ],
)
def test_donation_amounts(choice, custom, expected):
    form = DonationForm.model_validate({**DONOR, "amount_choice": choice, "custom_amount": custom})
    assert form.amount_rupees == expected


@pytest.mark.parametrize("custom", ["", "99", "500001", "12.50", "-500", "abc"])
def test_invalid_custom_amounts(custom):
    with pytest.raises(ValidationError) as exc_info:
        DonationForm.model_validate({**DONOR, "amount_choice": "custom", "custom_amount": custom})
    assert set(friendly_errors(exc_info.value)) == {"custom_amount"}


def test_donation_rejects_unknown_preset_and_frequency():
    with pytest.raises(ValidationError) as exc_info:
        DonationForm.model_validate({**DONOR, "amount_choice": "777", "frequency": "weekly"})
    assert set(friendly_errors(exc_info.value)) == {"amount_choice", "frequency"}
