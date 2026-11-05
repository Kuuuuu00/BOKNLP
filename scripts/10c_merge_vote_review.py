"""P2: merge reviewer judgments from the review workbook back into audit_votes_20.csv (guide C4).
uv run python scripts/10c_merge_vote_review.py [--allow-blank]
Checks: 1:1 on (meeting_date, sent_id, type), no missing/duplicate rows, allowed values per type. Exit 1 on any violation.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

from vote_review_common import ALLOWED, KEY

INTERIM = Path("data/interim")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default=str(INTERIM / "audit_votes_20.csv"))
    ap.add_argument("--review", default=str(INTERIM / "audit_votes_20_review.xlsx"))
    ap.add_argument("--out", default=str(INTERIM / "audit_votes_20_judged.csv"))
    ap.add_argument("--allow-blank", action="store_true", help="permit unfilled judgments (partial check)")
    args = ap.parse_args()
    base = pd.read_csv(args.audit, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    rev = pd.read_excel(args.review, dtype=str, keep_default_na=False)
    k = KEY
    rev["sent_id"] = rev["sent_id"].astype(int)
    base["sent_id"] = base["sent_id"].astype(int)
    errs = []
    for name, df in [("audit", base), ("review", rev)]:
        d = df[df.duplicated(k, keep=False)]
        if len(d):
            errs.append(f"{name}: {len(d)} duplicate keys")
    miss = base.merge(rev[k], on=k, how="left", indicator=True)
    miss = miss[miss["_merge"] == "left_only"]
    extra = rev.merge(base[k], on=k, how="left", indicator=True)
    extra = extra[extra["_merge"] == "left_only"]
    if len(miss):
        errs.append(f"{len(miss)} audit rows missing from review")
    if len(extra):
        errs.append(f"{len(extra)} review rows not in audit")
    m = base.drop(columns=["reviewer_judgment", "memo"]).merge(rev[k + ["reviewer_judgment", "memo"]], on=k, how="inner")
    for typ, allowed in ALLOWED.items():
        sub = m[m["type"] == typ]
        j = sub["reviewer_judgment"].str.strip()
        blank = (j == "").sum()
        bad = sub[~j.isin(allowed) & (j != "")]
        if blank and not args.allow_blank:
            errs.append(f"{typ}: {blank} blank judgments")
        if len(bad):
            errs.append(f"{typ}: {len(bad)} values outside {sorted(allowed)}: {sorted(set(bad['reviewer_judgment']))}")
    if errs:
        print("\n".join("ERROR " + e for e in errs))
        sys.exit(1)
    m.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(args.out, len(m))
    print(m.groupby(["type", "reviewer_judgment"]).size().to_string())


if __name__ == "__main__":
    main()
