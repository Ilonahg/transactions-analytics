from __future__ import annotations

import json
import logging
import math
import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, MutableMapping

logger = logging.getLogger(__name__)


def _jsonable(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Приводит список транзакций к JSON-совместимому виду:
    даты переводятся в строковый формат ISO.

    Args:
        records (List[Dict[str, Any]]): Список транзакций.

    Returns:
        List[Dict[str, Any]]: Транзакции с датами в строковом формате.
    """
    out: List[Dict[str, Any]] = []
    for tx in records:
        t = dict(tx)
        v = t.get("Дата операции")
        if isinstance(v, datetime):
            t["Дата операции"] = v.date().isoformat()
        elif isinstance(v, date):
            t["Дата операции"] = v.isoformat()
        out.append(t)
    return out


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму округлений (инвесткопилку) по расходам
    за указанный месяц.

    Args:
        month (str): Месяц в формате YYYY-MM.
        transactions (List[Dict[str, Any]]): Список транзакций.
        limit (int): Лимит округления (например 10).

    Returns:
        float: Общая сумма округлений.
    """
    y, m = map(int, month.split("-"))
    total = 0.0
    for tx in transactions:
        try:
            d = datetime.strptime(str(tx.get("Дата операции")), "%Y-%m-%d").date()
        except Exception:
            continue
        if d.year != y or d.month != m:
            continue
        amount = float(tx.get("Сумма операции", 0.0))
        if amount < 0:
            a = abs(amount)
            rem = a % limit
            delta = 0 if rem == 0 else (limit - rem)
            total += delta
    return round(total, 2)


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Выполняет простой поиск по строке в описании или категории транзакции.

    Args:
        query (str): Поисковая строка.
        transactions (List[Dict[str, Any]]): Список транзакций.

    Returns:
        str: JSON со списком найденных транзакций.
    """
    q = query.strip().lower()
    hits = []
    for tx in transactions:
        text = f"{tx.get('Описание', '')} {tx.get('Категория', '')}".lower()
        if q in text:
            hits.append(tx)
    return json.dumps(_jsonable(hits), ensure_ascii=False)


PHONE_RE = re.compile(r"(?:\+7|8)\s*\(?\d{3}\)?[\s-]*\d{2,3}[\s-]*\d{2}[\s-]*\d{2}")


def phone_number_search(transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет транзакции, в описании которых есть телефонные номера.

    Args:
        transactions (List[Dict[str, Any]]): Список транзакций.

    Returns:
        str: JSON с транзакциями, где найден телефон.
    """
    hits = []
    for tx in transactions:
        if PHONE_RE.search(str(tx.get("Описание", ""))):
            hits.append(tx)
    return json.dumps(_jsonable(hits), ensure_ascii=False)


P2P_NAME_RE = re.compile(r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.$")


def p2p_transfers_search(transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет переводы физическим лицам (категория «Переводы» + ФИО в описании).

    Args:
        transactions (List[Dict[str, Any]]): Список транзакций.

    Returns:
        str: JSON со списком переводов физлицам.
    """
    hits = []
    for tx in transactions:
        if str(tx.get("Категория")) != "Переводы":
            continue
        if P2P_NAME_RE.match(str(tx.get("Описание", "")).strip()):
            hits.append(tx)
    return json.dumps(_jsonable(hits), ensure_ascii=False)


def cashback_by_category(data: List[Dict[str, Any]], year: int, month: int) -> str:
    """
    Считает базовый кешбэк 1% по каждой категории за выбранный месяц.

    Args:
        data (List[Dict[str, Any]]): Список транзакций.
        year (int): Год.
        month (int): Месяц.

    Returns:
        str: JSON со словарём «категория -> кешбэк».
    """
    acc: MutableMapping[str, float] = defaultdict(float)
    for tx in data:
        try:
            d = datetime.strptime(str(tx.get("Дата операции")), "%Y-%m-%d").date()
        except Exception:
            continue
        if d.year != year or d.month != month:
            continue
        amount = float(tx.get("Сумма операции", 0.0))
        if amount < 0:
            cat = str(tx.get("Категория", ""))
            acc[cat] += abs(amount) * 0.01
    result = {cat: int(math.floor(val)) for cat, val in acc.items()}
    return json.dumps(result, ensure_ascii=False)
