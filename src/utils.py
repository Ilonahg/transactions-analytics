from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Mapping, Protocol, Sequence

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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Нормализует названия колонок датафрейма (приводит к ожидаемым).

    Args:
        df (pd.DataFrame): Исходный датафрейм.

    Returns:
        pd.DataFrame: Датафрейм с нормализованными названиями колонок.
    """
    mapping: Dict[str, str] = {}
    for want in EXPECTED_COLUMNS:
        for col in df.columns:
            if want in col:
                mapping[col] = EXPECTED_COLUMNS[want]
    return df.rename(columns=mapping)


def load_transactions_from_excel(path: str | None = None) -> pd.DataFrame:
    """
    Загружает транзакции из Excel-файла.

    Args:
        path (str | None): Путь к файлу. Если None — используется data/operations.xlsx.

    Returns:
        pd.DataFrame: Таблица транзакций.
    """
    if path is None:
        path = os.path.join("data", "operations.xlsx")
    df = pd.read_excel(path)
    df = normalize_columns(df)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"]).dt.date
    return df


def filter_by_date_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """
    Фильтрует транзакции по диапазону дат.

    Args:
        df (pd.DataFrame): Таблица транзакций.
        start (date): Начало диапазона.
        end (date): Конец диапазона.

    Returns:
        pd.DataFrame: Отфильтрованный датафрейм.
    """
    return df[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)].copy()


def parse_datetime_str(s: str) -> datetime:
    """
    Преобразует строку в datetime.

    Args:
        s (str): Дата и время в формате YYYY-MM-DD HH:MM:SS.

    Returns:
        datetime: Объект datetime.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def parse_date_str(s: str) -> date:
    """
    Преобразует строку в дату.

    Args:
        s (str): Дата в формате YYYY-MM-DD.

    Returns:
        date: Объект date.
    """
    return datetime.strptime(s, "%Y-%m-%d").date()


def period_start(d: date, range_type: str) -> date:
    """
    Возвращает дату начала периода (месяц, год или неделя).

    Args:
        d (date): Опорная дата.
        range_type (str): Тип периода ("M", "Y", "W").

    Returns:
        date: Дата начала периода.
    """
    if range_type == "M":
        return d.replace(day=1)
    if range_type == "Y":
        return d.replace(month=1, day=1)
    if range_type == "W":
        return d - timedelta(days=d.weekday())
    return date(1970, 1, 1)


def greeting_for_time(dt: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Args:
        dt (datetime): Время.

    Returns:
        str: Текст приветствия.
    """
    h = dt.hour
    if 5 <= h < 12:
        return "Доброе утро"
    if 12 <= h < 18:
        return "Добрый день"
    if 18 <= h < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def last4(card: str) -> str:
    """
    Возвращает последние 4 цифры номера карты.

    Args:
        card (str): Номер карты.

    Returns:
        str: Последние 4 цифры.
    """
    return card[-4:]


def is_expense(amount: float) -> bool:
    """
    Проверяет, является ли сумма расходом.

    Args:
        amount (float): Сумма транзакции.

    Returns:
        bool: True если расход.
    """
    return amount < 0


def is_income(amount: float) -> bool:
    """
    Проверяет, является ли сумма доходом.

    Args:
        amount (float): Сумма транзакции.

    Returns:
        bool: True если доход.
    """
    return amount > 0


def load_user_settings(path: str = "user_settings.json") -> Mapping[str, Sequence[str]]:
    """
    Загружает пользовательские настройки из файла JSON.

    Args:
        path (str): Путь к файлу настроек.

    Returns:
        Mapping[str, Sequence[str]]: Настройки пользователя.
    """
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}


class MarketDataProvider(Protocol):
    """
    Протокол для поставщика рыночных данных.
    """
    def get_currency_rates(self, currencies: Sequence[str]) -> Mapping[str, float]: ...
    def get_stock_prices(self, tickers: Sequence[str]) -> Mapping[str, float]: ...


@dataclass
class RequestsMarketDataProvider:
    """
    Провайдер рыночных данных на базе HTTP-запросов.
    """
    currency_api_url: str = os.getenv("CURRENCY_API", "https://open.er-api.com/v6/latest/RUB")
    stocks_api_url: str = os.getenv("STOCKS_API", "https://dummyjson.com/products")

    def get_currency_rates(self, currencies: Sequence[str]) -> Mapping[str, float]:
        """
        Возвращает курсы валют для указанных валют.

        Args:
            currencies (Sequence[str]): Список кодов валют.

        Returns:
            Mapping[str, float]: Курсы валют.
        """
        try:
            resp = requests.get(self.currency_api_url, timeout=10)
            data = resp.json()
            return {c: data["rates"].get(c, 0.0) for c in currencies}
        except Exception as e:
            logger.error("currency api error %s", e)
            return {c: 0.0 for c in currencies}

    def get_stock_prices(self, tickers: Sequence[str]) -> Mapping[str, float]:
        """
        Возвращает цены акций (заглушка — фиксированное значение).

        Args:
            tickers (Sequence[str]): Список тикеров.

        Returns:
            Mapping[str, float]: Цены акций.
        """
        try:
            return {t: 100.0 for t in tickers}
        except Exception as e:
            logger.error("stocks api error %s", e)
            return {t: 0.0 for t in tickers}
