"""P7: fetch market series. ECOS needs ECOS_API_KEY (the key sits in the URL path, so every message is masked).
  uv run --env-file .env python scripts/19_fetch_market_data.py discover
  uv run --env-file .env python scripts/19_fetch_market_data.py ecos --series ktb3y=817Y002:D:010200000 ...
  uv run python scripts/19_fetch_market_data.py fred
discover: lists ECOS statistic tables / items (name, cycle, start) to confirm codes by hand; nothing is hard-coded here.
Outputs: data/raw/market/<name>.csv (date,value,source,fetched_at), made read-only; RUNLOG.md gets rows and SHA-256.
This script never reads index/stance files.
"""
import argparse
import hashlib
import io
import json
import os
import stat
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/market")
RUNLOG = Path("data/interim/RUNLOG.md")
ECOS = "https://ecos.bok.or.kr/api"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
FRED_SERIES = {"fred_dgs2": "DGS2", "fred_dgs10": "DGS10", "fred_dfedtaru": "DFEDTARU"}


def key():
    k = os.environ.get("ECOS_API_KEY", "").strip()
    if not k:
        sys.exit("ECOS_API_KEY is not set (run with: uv run --env-file .env ...)")
    return k


def mask(text):
    k = os.environ.get("ECOS_API_KEY", "").strip()
    return str(text).replace(k, "***") if k else str(text)


def ecos_get(*parts):
    """GET {ECOS}/<service>/<key>/json/kr/... ; any exception is re-raised with the key masked and no traceback chain."""
    url = "/".join([ECOS, parts[0], key(), "json", "kr", *map(str, parts[1:])])
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            js = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # exception text may embed the URL
        raise SystemExit(f"ECOS request failed ({parts[0]}): {mask(type(e).__name__ + ': ' + str(e))}") from None
    if "RESULT" in js:
        raise SystemExit(f"ECOS error ({parts[0]}): {mask(js['RESULT'])}")
    return js


def ecos_rows(service, *parts, page=1000):
    out, start = [], 1
    while True:
        js = ecos_get(service, start, start + page - 1, *parts)
        blk = js[service]
        if not blk["row"]:
            raise SystemExit(f"ECOS returned an empty page for {service} before list_total_count was reached")
        out += blk["row"]
        if len(out) >= int(blk["list_total_count"]):
            return out
        start += page


def discover(args):
    tabs = pd.DataFrame(ecos_rows("StatisticTableList"))
    pat = "|".join(args.name_filter)
    tabs = tabs[tabs["STAT_NAME"].str.contains(pat, regex=True)]
    pd.set_option("display.width", 250, "display.max_colwidth", 80)
    print("== tables matching", pat, "==")
    print(tabs[["STAT_CODE", "STAT_NAME", "CYCLE" if "CYCLE" in tabs else "STAT_CODE"]].to_string(index=False))
    for code in args.stat_code:
        items = pd.DataFrame(ecos_rows("StatisticItemList", code))
        keep = items[items["ITEM_NAME"].str.contains("|".join(args.item_filter), regex=True)] if args.item_filter else items
        print(f"== items of {code} ==")
        print(keep[["STAT_CODE", "STAT_NAME", "ITEM_CODE", "ITEM_NAME", "CYCLE", "START_TIME", "END_TIME"]].to_string(index=False))


def save(name, df, source):
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / f"{name}.csv"
    if p.exists():
        os.chmod(p, stat.S_IWUSR | stat.S_IRUSR)
    df = df.assign(source=source, fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))[["date", "value", "source", "fetched_at"]]
    df.to_csv(p, index=False)
    os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    line = f"- {datetime.now().strftime('%Y-%m-%d')} P7 {p}: {len(df)} rows, {df['date'].min()}..{df['date'].max()}, SHA-256 `{sha}` ({source})\n"
    with open(RUNLOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())


def fetch_ecos(args):
    for spec in args.series:
        name, code = spec.split("=", 1)
        stat_code, cycle, item = code.split(":")
        end = args.end.replace("-", "")
        rows = ecos_rows("StatisticSearch", stat_code, cycle, args.start.replace("-", ""), end, item)
        df = pd.DataFrame(rows)
        d = pd.to_datetime(df["TIME"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
        out = pd.DataFrame({"date": d, "value": pd.to_numeric(df["DATA_VALUE"], errors="coerce")}).dropna().sort_values("date")
        save(f"ecos_{name}", out, f"ECOS {stat_code}/{cycle}/{item} ({df['ITEM_NAME1'].iloc[0]})")


def fetch_fred(args):
    for name, sid in FRED_SERIES.items():
        try:
            with urllib.request.urlopen(FRED.format(sid), timeout=60) as r:
                text = r.read().decode("utf-8")
        except Exception as e:
            raise SystemExit(f"FRED request failed ({sid}): {type(e).__name__}") from None
        df = pd.read_csv(io.StringIO(text))
        df.columns = ["date", "value"]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")  # '.' = no observation
        df = df.dropna()
        df = df[df["date"] >= args.start]
        save(name, df, f"FRED {sid} fredgraph.csv")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover")
    d.add_argument("--name-filter", nargs="+", default=["시장금리", "기준금리"])
    d.add_argument("--stat-code", nargs="*", default=[])
    d.add_argument("--item-filter", nargs="*", default=["국고채", "기준금리", "한국은행"])
    e = sub.add_parser("ecos")
    e.add_argument("--series", nargs="+", required=True, help="name=STAT_CODE:CYCLE:ITEM_CODE")
    e.add_argument("--start", default="2009-12-01")
    e.add_argument("--end", default=datetime.now().strftime("%Y-%m-%d"))
    f = sub.add_parser("fred")
    f.add_argument("--start", default="2009-12-01")
    args = ap.parse_args()
    {"discover": discover, "ecos": fetch_ecos, "fred": fetch_fred}[args.cmd](args)


if __name__ == "__main__":
    main()
