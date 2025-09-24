from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence

import pandas as pd
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

EXPECTED_COLUMNS = {
    "Дата операции": "Дата операции",
    "Категория": "Категория",
    "Описание": "Описание",
    "Сумма операции": "Сумма операции",
    "Карта": "Карта",
}


# ===== helpers for dataframe =====
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping: Dict[str, str] = {}
    for want in EXPECTED_COLUMNS:
        for col in df.columns:
            if want in col:
                mapping[col] = EXPECTED_COLUMNS[want]
    return df.rename(columns=mapping)


def load_transactions_from_excel(path: str | None = None) -> pd.DataFrame:
    if path is None:
        path = os.path.join("data", "operations.xlsx")
    df = pd.read_excel(path)
    df = normalize_columns(df)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"]).dt.date
    return df


def filter_by_date_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    return df[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)].copy()


# ===== time/date helpers =====
def parse_datetime_str(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def parse_date_str(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def period_start(d: date, range_type: str) -> date:
    if range_type == "M":
        return d.replace(day=1)
    if range_type == "Y":
        return d.replace(month=1, day=1)
    if range_type == "W":
        return d - timedelta(days=d.weekday())
    return date(1970, 1, 1)


def greeting_for_time(dt: datetime) -> str:
    h = dt.hour
    if 5 <= h < 12:
        return "Доброе утро"
    if 12 <= h < 18:
        return "Добрый день"
    if 18 <= h < 23:
        return "Добрый вечер"
    return "Доброй ночи"


# ===== transactions helpers =====
def last4(card: str) -> str:
    return card[-4:]


def is_expense(amount: float) -> bool:
    return amount < 0


def is_income(amount: float) -> bool:
    return amount > 0


# ===== settings =====
def load_user_settings(path: str = "user_settings.json") -> Mapping[str, Sequence[str]]:
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}


# ===== provider for market data =====
class MarketDataProvider(Protocol):
    def get_currency_rates(self, currencies: Sequence[str]) -> Mapping[str, float]: ...

    def get_stock_prices(self, tickers: Sequence[str]) -> Mapping[str, float]: ...


@dataclass
class RequestsMarketDataProvider:
    currency_api_url: str = os.getenv("CURRENCY_API", "https://open.er-api.com/v6/latest/RUB")
    stocks_api_url: str = os.getenv("STOCKS_API", "https://dummyjson.com/products")

    def get_currency_rates(self, currencies: Sequence[str]) -> Mapping[str, float]:
        try:
            resp = requests.get(self.currency_api_url, timeout=10)
            data = resp.json()
            return {c: data["rates"].get(c, 0.0) for c in currencies}
        except Exception as e:
            logger.error("currency api error %s", e)
            return {c: 0.0 for c in currencies}

    def get_stock_prices(self, tickers: Sequence[str]) -> Mapping[str, float]:
        try:
            # заглушка — вместо реального API
            return {t: 100.0 for t in tickers}
        except Exception as e:
            logger.error("stocks api error %s", e)
            return {t: 0.0 for t in tickers}
