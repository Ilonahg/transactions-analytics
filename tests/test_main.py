import pytest
from unittest.mock import patch
import src.main as main


def run_cli(monkeypatch, args, transactions_df):
    """Запуск CLI с подменой загрузки Excel"""
    # Подменяем именно в src.main
    monkeypatch.setattr("src.main.load_transactions_from_excel", lambda: transactions_df)
    monkeypatch.setattr("sys.argv", ["prog"] + args)
    outputs = []

    def fake_print(*a, **k):
        outputs.append(" ".join(map(str, a)))

    monkeypatch.setattr("builtins.print", fake_print)
    main.cli()
    return outputs


def test_cli_home(monkeypatch, transactions_df):
    out = run_cli(monkeypatch, ["home", "2023-05-20 12:00:00"], transactions_df)
    assert any("greeting" in x.lower() for x in out)


def test_cli_events(monkeypatch, transactions_df):
    out = run_cli(monkeypatch, ["events", "2023-05-20", "--range", "M"], transactions_df)
    assert out


@pytest.mark.parametrize("rtype", ["category", "weekday", "workday"])
def test_cli_reports(monkeypatch, transactions_df, rtype):
    args = ["report", rtype]
    if rtype == "category":
        args += ["Супермаркеты", "--date", "2023-05-20"]
    else:
        args += ["--date", "2023-05-20"]
    out = run_cli(monkeypatch, args, transactions_df)
    assert out


@pytest.mark.parametrize("stype,args", [
    ("invest", ["2023-05", "--limit", "10"]),
    ("search", ["Лента"]),
    ("phones", []),
    ("p2p", []),
    ("cashback", ["--year", "2023", "--month", "5"]),
])
def test_cli_services(monkeypatch, transactions_df, stype, args):
    out = run_cli(monkeypatch, ["service", stype] + args, transactions_df)
    assert out


def test_cli_invest_with_patch(monkeypatch, transactions_df):
    """Проверка Mock для invest"""
    monkeypatch.setattr("src.main.load_transactions_from_excel", lambda: transactions_df)
    with patch("src.services.investment_bank", return_value="INVEST_OK") as mock_func:
        out = run_cli(monkeypatch, ["service", "invest", "2023-05"], transactions_df)
        mock_func.assert_called_once()
        assert "INVEST_OK" in out[0]


def test_cli_cashback_with_patch(monkeypatch, transactions_df):
    """Проверка Mock для cashback"""
    monkeypatch.setattr("src.main.load_transactions_from_excel", lambda: transactions_df)
    with patch("src.services.cashback_by_category", return_value="CASHBACK_OK") as mock_func:
        out = run_cli(monkeypatch, ["service", "cashback", "--year", "2023", "--month", "5"], transactions_df)
        mock_func.assert_called_once()
        assert "CASHBACK_OK" in out[0]
