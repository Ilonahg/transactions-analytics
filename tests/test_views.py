from __future__ import annotations

import json

from src.utils import RequestsMarketDataProvider
from src.views import events, home


class DummyProvider(RequestsMarketDataProvider):
    def get_currency_rates(self, currencies):  # type: ignore[override]
        return {c: 100.0 for c in currencies}

    def get_stock_prices(self, tickers):  # type: ignore[override]
        return {t: 10.0 for t in tickers}


def test_home(transactions_df):
    dt = "2023-05-20 12:00:00"
    out = json.loads(home(dt, df=transactions_df, provider=DummyProvider()))
    assert "greeting" in out
    assert "cards" in out and len(out["cards"]) >= 1
    assert "top_transactions" in out and len(out["top_transactions"]) == 5
    assert "currency_rates" in out and "stock_prices" in out


def test_events(transactions_df):
    out = json.loads(events(transactions_df, "2023-05-20", "M", provider=DummyProvider()))
    assert out["expenses"]["total_amount"] > 0
    assert out["income"]["total_amount"] >= 30000
