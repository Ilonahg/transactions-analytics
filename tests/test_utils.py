from __future__ import annotations

from datetime import date

from src.utils import last4, period_start


def test_last4():
    assert last4("**** 1234") == "1234"
    assert last4("4111 1111 1111 4242") == "4242"
    assert last4("") == ""


def test_period_start():
    d = date(2023, 5, 20)
    assert period_start(d, "M") == date(2023, 5, 1)
    assert period_start(d, "Y") == date(2023, 1, 1)
    assert period_start(d, "W") == date(2023, 5, 15)
