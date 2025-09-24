from __future__ import annotations

import json

from src.services import (
    cashback_by_category,
    investment_bank,
    phone_number_search,
    p2p_transfers_search,
    simple_search,
)


def test_investment_bank(transactions_list):
    total = investment_bank("2023-05", transactions_list, limit=50)
    assert total >= 0


def test_simple_search(transactions_list):
    res = json.loads(simple_search("супермаркет", transactions_list))
    assert isinstance(res, list)


def test_phone_number_search(transactions_list):
    res = json.loads(phone_number_search(transactions_list))
    assert any("МТС" in r.get("Описание", "") for r in res)


def test_p2p_transfers_search(transactions_list):
    res = json.loads(p2p_transfers_search(transactions_list))
    assert len(res) >= 1


def test_cashback_by_category(transactions_list):
    res = json.loads(cashback_by_category(transactions_list, 2023, 5))
    assert isinstance(res, dict)
    assert any(v >= 0 for v in res.values())
