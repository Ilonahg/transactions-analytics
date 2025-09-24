from __future__ import annotations

import json
import logging
from typing import Optional

import pandas as pd

from .utils import (
    RequestsMarketDataProvider,
    filter_by_date_range,
    greeting_for_time,
    is_expense,
    is_income,
    last4,
    load_transactions_from_excel,
    load_user_settings,
    parse_datetime_str,
    parse_date_str,
    period_start,
)

logger = logging.getLogger(__name__)


def home(
    datetime_str: str,
    *,
    df: Optional[pd.DataFrame] = None,
    provider: Optional[RequestsMarketDataProvider] = None,
) -> str:
    """Страница «Главная»: приветствие, сводка по картам, топ-5, курсы и акции."""
    dt = parse_datetime_str(datetime_str)
    start = dt.replace(day=1).date()
    end = dt.date()

    # ВАЖНО: не использовать "df or ..." для DataFrame
    if df is None:
        df = load_transactions_from_excel()

    df_range = filter_by_date_range(df, start, end)

    # Сводка по картам: расходы и кешбэк (1 руб/100 руб)
    cards = []
    for card, grp in df_range.groupby("Карта"):
        expenses = grp[grp["Сумма операции"].apply(is_expense)]["Сумма операции"].abs().sum()
        cashback = int(expenses // 100)
        cards.append(
            {
                "card_last4": last4(str(card)),
                "total_expenses": int(round(float(expenses))),
                "cashback": cashback,
            }
        )

    # Топ-5 транзакций по абсолютной сумме
    top5 = (
        df_range.assign(abs_amount=df_range["Сумма операции"].abs()).sort_values("abs_amount", ascending=False).head(5)
    )
    top_transactions = [
        {
            "date": str(r["Дата операции"]),
            "card_last4": last4(str(r.get("Карта", ""))),
            "amount": float(r.get("Сумма операции", 0.0)),
            "description": r.get("Описание", ""),
            "category": r.get("Категория", ""),
        }
        for _, r in top5.iterrows()
    ]

    # Рыночные данные
    settings = load_user_settings()
    provider = provider or RequestsMarketDataProvider()
    currency_rates = provider.get_currency_rates(settings.get("user_currencies", []))
    stock_prices = provider.get_stock_prices(settings.get("user_stocks", []))

    result = {
        "greeting": greeting_for_time(dt),
        "cards": cards,
        "top_transactions": top_transactions,  # ключ, который ждут тесты
        "currency_rates": [{"currency": c, "rate": float(r)} for c, r in currency_rates.items()],
        "stock_prices": [{"stock": t, "price": float(p)} for t, p in stock_prices.items()],
    }
    return json.dumps(result, ensure_ascii=False)


def events(
    df: pd.DataFrame,
    date_str: str,
    range_code: str = "M",
    *,
    provider: Optional[RequestsMarketDataProvider] = None,
) -> str:
    """Страница «События»: расходы/поступления + курсы/акции за период."""
    end = parse_date_str(date_str)
    start = period_start(end, range_code)
    df_range = filter_by_date_range(df, start, end)

    # Расходы
    exp = df_range[df_range["Сумма операции"].apply(is_expense)].copy()
    exp["abs"] = exp["Сумма операции"].abs()
    expenses_total = int(round(exp["abs"].sum()))

    main_exp = exp[~exp["Категория"].isin(["Наличные", "Переводы"])]
    main_by_cat = main_exp.groupby("Категория")["abs"].sum().sort_values(ascending=False).reset_index()
    top7 = main_by_cat.head(7)
    main_list = [{"category": r["Категория"], "amount": int(round(r["abs"]))} for _, r in top7.iterrows()]
    if len(main_by_cat) > 7:
        rest = int(round(main_by_cat["abs"][7:].sum()))
        main_list.append({"category": "Остальное", "amount": rest})

    transfers_cash = (
        exp[exp["Категория"].isin(["Наличные", "Переводы"])]
        .groupby("Категория")["abs"]
        .sum()
        .sort_values(ascending=False)
    )
    transfers_cash_list = (
        transfers_cash.reset_index()
        .rename(columns={"abs": "amount"})
        .assign(amount=lambda x: x["amount"].round().astype(int))
        .to_dict(orient="records")
    )

    # Доходы
    inc = df_range[df_range["Сумма операции"].apply(is_income)].copy()
    inc["amount"] = inc["Сумма операции"].astype(float)
    income_total = int(round(inc["amount"].sum()))
    income_main = inc.groupby("Категория")["amount"].sum().sort_values(ascending=False).reset_index()
    income_main_list = [
        {"category": r["Категория"], "amount": int(round(r["amount"]))} for _, r in income_main.iterrows()
    ]

    # Рыночные данные
    settings = load_user_settings()
    provider = provider or RequestsMarketDataProvider()
    currency_rates = provider.get_currency_rates(settings.get("user_currencies", []))
    stock_prices = provider.get_stock_prices(settings.get("user_stocks", []))

    result = {
        "expenses": {
            "total_amount": expenses_total,
            "main": main_list,
            "transfers_and_cash": transfers_cash_list,
        },
        "income": {
            "total_amount": income_total,
            "main": income_main_list,
        },
        "currency_rates": [{"currency": c, "rate": float(r)} for c, r in currency_rates.items()],
        "stock_prices": [{"stock": t, "price": float(p)} for t, p in stock_prices.items()],
    }
    return json.dumps(result, ensure_ascii=False)
