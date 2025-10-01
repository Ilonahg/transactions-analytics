from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_report(filename: Optional[str] = None):
    """
    Декоратор для сохранения отчётов в файл (xlsx или json).

    Args:
        filename (Optional[str]): Имя файла для сохранения. Если None —
            имя формируется автоматически.

    Returns:
        Callable: Обёртка для функции-отчёта.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            os.makedirs("reports", exist_ok=True)
            result = func(*args, **kwargs)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = filename
            if not out:
                ext = "xlsx" if isinstance(result, pd.DataFrame) else "json"
                out = os.path.join("reports", f"{func.__name__}_{ts}.{ext}")
            if isinstance(result, pd.DataFrame):
                result.to_excel(out, index=False)
            else:
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info("Report saved to %s", out)
            return result

        return wrapper

    return decorator


def _three_months_ago_start(d: date) -> date:
    """
    Возвращает первый день месяца, три месяца назад (включая текущий).

    Args:
        d (date): Опорная дата.

    Returns:
        date: Дата начала периода.
    """
    month = ((d.month - 3 - 1) % 12) + 1
    year = d.year + ((d.month - 3 - 1) // 12)
    return date(year, month, 1)


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date_str: Optional[str] = None) -> pd.DataFrame:
    """
    Траты по категории за последние 3 месяца от указанной даты.

    Args:
        transactions (pd.DataFrame): Таблица транзакций.
        category (str): Название категории.
        date_str (Optional[str]): Дата отсчёта (формат YYYY-MM-DD). Если None — берётся текущая.

    Returns:
        pd.DataFrame: Сводная таблица трат по месяцам.
    """
    ref = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    start = _three_months_ago_start(ref)
    mask = (transactions["Дата операции"] >= start) & (transactions["Дата операции"] <= ref)
    df = transactions.loc[mask].copy()
    df = df[(df["Категория"] == category) & (df["Сумма операции"] < 0)]
    df["Период"] = pd.to_datetime(df["Дата операции"]).dt.to_period("M").astype(str)
    agg = df.groupby("Период")["Сумма операции"].sum().abs().round(2).reset_index(name="Сумма")
    return agg


@save_report()
def spending_by_weekday(transactions: pd.DataFrame, date_str: Optional[str] = None) -> pd.DataFrame:
    """
    Средние дневные траты по дням недели за последние 3 месяца.

    Args:
        transactions (pd.DataFrame): Таблица транзакций.
        date_str (Optional[str]): Опорная дата. Если None — берётся текущая.

    Returns:
        pd.DataFrame: Таблица со средними тратами по дням недели.
    """
    ref = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    start = _three_months_ago_start(ref)
    df = transactions[(transactions["Дата операции"] >= start) & (transactions["Дата операции"] <= ref)].copy()
    df = df[df["Сумма операции"] < 0]
    df["day"] = pd.to_datetime(df["Дата операции"]).dt.date
    daily = df.groupby("day")["Сумма операции"].sum().abs().reset_index()
    daily["w"] = pd.to_datetime(daily["day"]).dt.weekday
    names = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
    out = daily.groupby("w")["Сумма операции"].mean().round(2).reset_index()
    out["День недели"] = out["w"].map(names)
    out = out.rename(columns={"Сумма операции": "Средние траты"})[["День недели", "Средние траты"]]
    return out


@save_report()
def spending_by_workday(transactions: pd.DataFrame, date_str: Optional[str] = None) -> pd.DataFrame:
    """
    Средние дневные траты в рабочие и выходные дни за последние 3 месяца.

    Args:
        transactions (pd.DataFrame): Таблица транзакций.
        date_str (Optional[str]): Опорная дата. Если None — берётся текущая.

    Returns:
        pd.DataFrame: Таблица со средними тратами по типу дня.
    """
    ref = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    start = _three_months_ago_start(ref)
    df = transactions[(transactions["Дата операции"] >= start) & (transactions["Дата операции"] <= ref)].copy()
    df = df[df["Сумма операции"] < 0]
    df["day"] = pd.to_datetime(df["Дата операции"]).dt.date
    daily = df.groupby("day")["Сумма операции"].sum().abs().reset_index()
    daily["w"] = pd.to_datetime(daily["day"]).dt.weekday
    daily["Тип дня"] = daily["w"].apply(lambda x: "Рабочий" if x < 5 else "Выходной")
    out = daily.groupby("Тип дня")["Сумма операции"].mean().round(2).reset_index()
    return out.rename(columns={"Сумма операции": "Средние траты"})
