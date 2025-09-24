from __future__ import annotations

import argparse
import logging

from . import reports as reports_mod
from . import services as services_mod
from . import views as views_mod
from .utils import load_transactions_from_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def cli() -> None:
    parser = argparse.ArgumentParser(description="Transactions analytics CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Home
    home_p = sub.add_parser("home")
    home_p.add_argument("datetime", help="YYYY-MM-DD HH:MM:SS")

    # Events
    events_p = sub.add_parser("events")
    events_p.add_argument("date", help="YYYY-MM-DD")
    events_p.add_argument("--range", choices=["W", "M", "Y", "ALL"], default="M")

    # Reports
    rep = sub.add_subparsers(dest="report", required=False)

    rep_cmd = sub.add_parser("report")
    rep_sub = rep_cmd.add_subparsers(dest="rtype", required=True)

    rep_cat = rep_sub.add_parser("category")
    rep_cat.add_argument("category")
    rep_cat.add_argument("--date", default=None)

    rep_wd = rep_sub.add_parser("weekday")
    rep_wd.add_argument("--date", default=None)

    rep_work = rep_sub.add_parser("workday")
    rep_work.add_argument("--date", default=None)

    # Services
    srv_cmd = sub.add_parser("service")
    srv_sub = srv_cmd.add_subparsers(dest="stype", required=True)

    srv_invest = srv_sub.add_parser("invest")
    srv_invest.add_argument("month", help="YYYY-MM")
    srv_invest.add_argument("--limit", type=int, default=50)

    srv_search = srv_sub.add_parser("search")
    srv_search.add_argument("query")

    srv_sub.add_parser("phones")
    srv_sub.add_parser("p2p")

    srv_cashback = srv_sub.add_parser("cashback")
    srv_cashback.add_argument("--year", type=int, required=True)
    srv_cashback.add_argument("--month", type=int, required=True)

    args = parser.parse_args()
    df = load_transactions_from_excel()

    if args.cmd == "home":
        print(views_mod.home(args.datetime, df=df))
    elif args.cmd == "events":
        print(views_mod.events(df, args.date, args.range))
    elif args.cmd == "report":
        if args.rtype == "category":
            out = reports_mod.spending_by_category(df, args.category, args.date)
        elif args.rtype == "weekday":
            out = reports_mod.spending_by_weekday(df, args.date)
        else:
            out = reports_mod.spending_by_workday(df, args.date)
        print(out.to_string(index=False))
    elif args.cmd == "service":
        data = df.to_dict(orient="records")
        if args.stype == "invest":
            print(services_mod.investment_bank(args.month, data, args.limit))
        elif args.stype == "search":
            print(services_mod.simple_search(args.query, data))
        elif args.stype == "phones":
            print(services_mod.phone_number_search(data))
        elif args.stype == "p2p":
            print(services_mod.p2p_transfers_search(data))
        elif args.stype == "cashback":
            print(services_mod.cashback_by_category(data, args.year, args.month))


if __name__ == "__main__":
    cli()
