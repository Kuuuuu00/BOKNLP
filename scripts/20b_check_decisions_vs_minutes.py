"""P7 check: compare d_i / bok_rate in market_events.csv with the decision text of each minutes PDF ('Monetary Policy Decision' box).
uv run python scripts/20b_check_decisions_vs_minutes.py
Reads the raw PDFs (read-only) and market_events.csv only; no stance/index file. Meetings whose decision text cannot be parsed are listed as
unverifiable, never guessed. Direction word after 'decided today to' / 'decided to'; level from 'from X% to Y%' or 'at ... (X%)'.
"""
import argparse
import re
from pathlib import Path

import pandas as pd
import pymupdf

INTERIM = Path("data/interim")
DEC = re.compile(r"decided(?: today)?\s*(?:□\s*)?to\s+(?:□\s*)?(raise|lower|cut|increase|maintain|keep|hold|leave|reduce)\b(.{0,160})", re.I)
FROM_TO = re.compile(r"from\s+(\d+(?:\.\d+)?)\s?%(?:\s+of its current level)?\s+to\s+(\d+(?:\.\d+)?)\s?%", re.I)
LEVEL = re.compile(r"(\d+(?:\.\d+)?)\s?%")
BY_BP = re.compile(r"by\s+(\d+(?:\.\d+)?)\s+basis points?|by\s+(0\.\d+)\s+(?:of a\s+)?percentage point", re.I)
DIR = {"raise": 1, "increase": 1, "lower": -1, "cut": -1, "reduce": -1, "maintain": 0, "keep": 0, "hold": 0, "leave": 0}


def parse_pdf(path):
    t = re.sub(r"\s+", " ", " ".join(p.get_text() for p in pymupdf.open(path)))
    hits = [m for m in DEC.finditer(t) if "base rate" in m.group(0).lower()]
    if not hits:
        return None
    m = hits[-1]  # the decision box sits at the end of the document
    tail = m.group(2)
    ft = FROM_TO.search(tail)
    lv = LEVEL.search(tail)
    by = BY_BP.search(tail)
    bp = None
    if by:
        bp = float(by.group(1)) if by.group(1) else round(float(by.group(2)) * 100)
    return {"dir": DIR[m.group(1).lower()], "from": float(ft.group(1)) if ft else None, "to": float(ft.group(2)) if ft else (float(lv.group(1)) if lv else None), "bp": bp,
            "text": re.sub(r"\s+", " ", m.group(0))[:140]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default="data/raw/pdf")
    ap.add_argument("--events", default=str(INTERIM / "market_events.csv"))
    ap.add_argument("--out", default=str(INTERIM / "decision_check.csv"))
    args = ap.parse_args()
    ev = pd.read_csv(args.events, dtype={"meeting_date": str})
    rows = []
    for _, r in ev.iterrows():
        p = parse_pdf(Path(args.pdf_dir) / f"bok_minutes_{r['meeting_date']}.pdf")
        sign = 0 if r["d_i"] == 0 else (1 if r["d_i"] > 0 else -1)
        if p is None or pd.isna(r["d_i"]):
            rows.append({"meeting_date": r["meeting_date"], "d_i": r["d_i"], "bok_rate": r["bok_rate"], "status": "unverifiable (no parsable decision text)"})
            continue
        ok_dir = p["dir"] == sign
        ok_bp = p["bp"] is None or abs(p["bp"] - abs(r["d_i"])) < 1e-6 or p["dir"] == 0
        ok_lvl = p["to"] is None or abs(p["to"] - r["bok_rate"]) < 1e-6
        rows.append({"meeting_date": r["meeting_date"], "d_i": r["d_i"], "bok_rate": r["bok_rate"], "minutes_dir": p["dir"], "minutes_bp": p["bp"],
                     "minutes_from": p["from"], "minutes_to": p["to"], "status": "match" if (ok_dir and ok_bp and ok_lvl) else "MISMATCH", "text": p["text"]})
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(out["status"].value_counts().to_string())
    print("d_i != 0 meetings by status:", out[out["d_i"] != 0]["status"].value_counts().to_dict())
    for _, r in out[out["status"] != "match"].iterrows():
        print(r["meeting_date"], "d_i", r["d_i"], "bok_rate", r["bok_rate"], r["status"], "|", r.get("text", ""))


if __name__ == "__main__":
    main()
