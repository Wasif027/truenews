from __future__ import annotations

import argparse
import json
import logging

import httpx

from app.config import get_settings
from app.ingest.pipeline import recategorize, run, run_all
from app.ingest.sources import sources_for

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 TrueNewsBot/0.1"
    )
}


def _reset() -> None:
    """Drop every table and recreate the empty schema. Use after changing the
    clustering threshold, so stories are rebuilt from scratch."""
    from sqlmodel import SQLModel

    from app.db import engine, init_db

    SQLModel.metadata.drop_all(engine)
    init_db()
    print("database reset: schema recreated, no rows")


def _verify_feeds(country: str | None) -> None:
    countries = [country] if country else get_settings().country_list
    for c in countries:
        print(f"# {c}")
        for cfg in sources_for(c):
            for feed_url in cfg.feeds:
                try:
                    r = httpx.get(feed_url, headers=_UA, timeout=20.0, follow_redirects=True)
                    looks_xml = b"<rss" in r.content[:2000] or b"<feed" in r.content[:2000]
                    note = "ok" if r.status_code == 200 and looks_xml else "check payload"
                    status = str(r.status_code)
                except httpx.HTTPError as exc:
                    status, note = "ERR", type(exc).__name__
                print(f"  {cfg.slug:16s} {status:4s} {note:14s} {feed_url}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="truenews")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_ingest = sub.add_parser("ingest", help="ingest all configured countries (or --country)")
    p_ingest.add_argument("--country", default=None)
    p_verify = sub.add_parser("verify-feeds", help="check that configured RSS feeds respond")
    p_verify.add_argument("--country", default=None)
    sub.add_parser("reset", help="drop all data and recreate the empty schema")
    sub.add_parser("recategorize", help="re-run category rules on stored data")

    args = parser.parse_args()
    country = getattr(args, "country", None)

    if args.cmd == "ingest":
        result = run(country) if country else run_all()
        print(json.dumps(result, indent=2))
    elif args.cmd == "verify-feeds":
        _verify_feeds(country)
    elif args.cmd == "reset":
        _reset()
    elif args.cmd == "recategorize":
        print(json.dumps(recategorize(), indent=2))


if __name__ == "__main__":
    main()
