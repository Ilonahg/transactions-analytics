from __future__ import annotations

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday


def test_spending_by_category(transactions_df):
    out = spending_by_category(transactions_df, "Супермаркеты", date_str="2023-05-20")
    assert not out.empty


def test_spending_by_weekday(transactions_df):
    out = spending_by_weekday(transactions_df, date_str="2023-05-20")
    assert set(out.columns) == {"День недели", "Средние траты"}


def test_spending_by_workday(transactions_df):
    out = spending_by_workday(transactions_df, date_str="2023-05-20")
    assert set(out.columns) == {"Тип дня", "Средние траты"}
