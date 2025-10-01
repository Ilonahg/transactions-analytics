from unittest.mock import patch
import pandas as pd
import pytest
from datetime import date
from src.utils import load_transactions_from_excel, last4, period_start


@patch("src.utils.pd.read_excel")
def test_load_transactions_mocked(mock_read_excel):
    """Тест загрузки транзакций с моканым pd.read_excel"""
    mock_read_excel.return_value = pd.DataFrame(
        [{
            "Дата операции": "2023-01-01",
            "Категория": "Еда",
            "Описание": "Test",
            "Сумма операции": -100,
            "Карта": "**** 1111"
        }]
    )
    df = load_transactions_from_excel("fake.xlsx")
    assert not df.empty
    assert "Категория" in df.columns
    mock_read_excel.assert_called_once()


@pytest.mark.parametrize("card,expected", [
    ("**** 1234", "1234"),
    ("4111 1111 1111 4242", "4242"),
    ("", ""),
])
def test_last4_param(card, expected):
    """Параметризация теста для last4"""
    assert last4(card) == expected


@pytest.mark.parametrize("d,range_code,expected", [
    (date(2023, 5, 20), "M", date(2023, 5, 1)),
    (date(2023, 5, 20), "Y", date(2023, 1, 1)),
    (date(2023, 5, 20), "W", date(2023, 5, 15)),
])
def test_period_start_param(d, range_code, expected):
    """Параметризация теста для period_start"""
    assert period_start(d, range_code) == expected
