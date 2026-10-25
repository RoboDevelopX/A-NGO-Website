from datetime import datetime

import pytest

from app.formatting import format_date, format_datetime, format_inr, reading_time_minutes, to_ist


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, "₹0"),
        (500, "₹500"),
        (1000, "₹1,000"),
        (25000, "₹25,000"),
        (100000, "₹1,00,000"),
        (1250000, "₹12,50,000"),
        (123456789, "₹12,34,56,789"),
    ],
)
def test_format_inr_uses_indian_grouping(amount, expected):
    assert format_inr(amount) == expected


def test_format_inr_without_symbol():
    assert format_inr(100000, symbol=False) == "1,00,000"


def test_to_ist_converts_naive_utc():
    local = to_ist(datetime(2026, 1, 1, 0, 0))
    assert (local.hour, local.minute) == (5, 30)


def test_format_date_and_datetime():
    dt = datetime(2026, 3, 4, 4, 30)  # 10:00 IST
    assert format_date(dt) == "4 Mar 2026"
    assert format_datetime(dt) == "Wed 4 Mar 2026, 10:00 AM IST"


@pytest.mark.parametrize(("words", "minutes"), [(0, 1), (1, 1), (200, 1), (201, 2), (1000, 5)])
def test_reading_time(words, minutes):
    assert reading_time_minutes(" ".join(["word"] * words)) == minutes
