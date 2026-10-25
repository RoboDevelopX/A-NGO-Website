import pytest

from app.services.payments import (
    DEMO_DECLINE_AMOUNT_PAISE,
    Frequency,
    MockPaymentProvider,
    PaymentProvider,
    PaymentRequest,
    PaymentStatus,
)


def request(amount_paise=100_000, key="k1", frequency=Frequency.ONE_TIME) -> PaymentRequest:
    return PaymentRequest(
        amount_paise=amount_paise,
        currency="INR",
        frequency=frequency,
        donor_name="Asha Nair",
        donor_email="asha@example.com",
        idempotency_key=key,
    )


def test_mock_provider_implements_the_interface():
    assert isinstance(MockPaymentProvider(), PaymentProvider)
    with pytest.raises(TypeError):
        PaymentProvider()  # abstract: can't be used without an implementation


def test_successful_one_time_and_monthly_charges():
    provider = MockPaymentProvider()
    one_time = provider.charge(request(key="a"))
    monthly = provider.charge(request(key="b", frequency=Frequency.MONTHLY))
    assert one_time.succeeded and one_time.provider_ref.startswith("mock_pay_")
    assert monthly.succeeded and monthly.provider_ref.startswith("mock_sub_")


def test_demo_decline_amount_is_declined_with_a_message():
    result = MockPaymentProvider().charge(request(DEMO_DECLINE_AMOUNT_PAISE))
    assert result.status is PaymentStatus.DECLINED
    assert not result.succeeded
    assert "declined" in result.message


def test_idempotency_key_prevents_double_charges():
    provider = MockPaymentProvider()
    first = provider.charge(request(key="same"))
    second = provider.charge(request(key="same"))
    assert first == second
    assert provider.charges == 1


def test_configurable_declines_and_input_checks():
    provider = MockPaymentProvider(decline_amounts_paise=frozenset({50_000}))
    assert not provider.charge(request(50_000, key="x")).succeeded
    assert provider.charge(request(DEMO_DECLINE_AMOUNT_PAISE, key="y")).succeeded
    with pytest.raises(ValueError):
        provider.charge(request(0, key="z"))


def test_payment_request_has_no_card_fields():
    fields = set(PaymentRequest.__dataclass_fields__)
    assert not fields & {"card", "card_number", "cvc", "cvv", "expiry", "pan"}
