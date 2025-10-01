from unittest.mock import patch
import pandas as pd
from src.reports import spending_by_category
import datetime


@patch("src.reports.datetime")
def test_spending_by_category_mocked_datetime(mock_dt, transactions_df):
    """Мокаем datetime.now() для стабильности теста"""
    mock_dt.now.return_value = datetime.datetime(2023, 5, 20, 12, 0, 0)
    mock_dt.strptime = datetime.datetime.strptime
    mock_dt.date = datetime.date

    df = spending_by_category(transactions_df, "Супермаркеты", date_str="2023-05-20")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
