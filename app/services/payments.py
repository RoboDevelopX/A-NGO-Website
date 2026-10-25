"""Payments behind an interface, with a mock implementation only.

This project must never take real money or touch card data, so the only implementation is
``MockPaymentProvider``. A real integration would add, for example, a provider that creates
a hosted-checkout session (Razorpay or Stripe Checkout). With hosted checkout the card form
lives on the provider's domain, card numbers never reach our server, and the routes and
templates that call ``PaymentProvider.charge`` would not need to change shape.
"""

from __future__ import annotations

import secrets
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class Frequency(StrEnum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    DECLINED = "declined"


@dataclass(frozen=True)
class PaymentRequest:
    amount_paise: int  # integer minor units: never use floats for money
    currency: str
    frequency: Frequency
    donor_name: str
    donor_email: str
    idempotency_key: str  # the same key must never charge twice


@dataclass(frozen=True)
class PaymentResult:
    status: PaymentStatus
    provider_ref: str
    message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status is PaymentStatus.SUCCEEDED


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def charge(self, request: PaymentRequest) -> PaymentResult:
        """Take a one-time payment or start a monthly subscription."""


# ₹1,313 always declines so the failure path can be demonstrated in the UI.
DEMO_DECLINE_AMOUNT_PAISE = 1313_00


class MockPaymentProvider(PaymentProvider):
    """Approves every payment except configured "decline" amounts. Moves no money."""

    name = "mock"

    def __init__(self, decline_amounts_paise: frozenset[int] | None = None) -> None:
        if decline_amounts_paise is None:
            decline_amounts_paise = frozenset({DEMO_DECLINE_AMOUNT_PAISE})
        self.decline_amounts_paise = decline_amounts_paise
        # Mirrors real providers: replaying an idempotency key returns the original result.
        self._results: dict[str, PaymentResult] = {}
        self._lock = threading.Lock()
        self.charges = 0

    def charge(self, request: PaymentRequest) -> PaymentResult:
        if request.amount_paise <= 0:
            raise ValueError("amount must be positive")
        with self._lock:
            if request.idempotency_key in self._results:
                return self._results[request.idempotency_key]
            self.charges += 1
            prefix = "mock_sub_" if request.frequency is Frequency.MONTHLY else "mock_pay_"
            ref = prefix + secrets.token_hex(8)
            if request.amount_paise in self.decline_amounts_paise:
                result = PaymentResult(
                    PaymentStatus.DECLINED,
                    ref,
                    "Your bank declined this payment. (Demo: ₹1,313 always declines.)",
                )
            else:
                result = PaymentResult(PaymentStatus.SUCCEEDED, ref)
            self._results[request.idempotency_key] = result
            return result
