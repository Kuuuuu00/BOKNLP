"""P2: aggregate the 20-document vote review (guide C4) from audit_votes_20_judged.csv.
uv run python scripts/10d_aggregate_vote_audit.py
Outputs: data/processed/table_vote_audit.csv (+ console table), data/processed/vote_audit_index_effect.csv.
Recall is an UPPER bound: sentences outside the candidate set (no 'Base Rate') are never reviewed, so misses there are unobserved.
Cause codes (S/F/N/O, R/C/Q) are parsed from memo only when present; memo without a code is listed verbatim, never guessed.
"""
import argparse
import re
from pathlib import Path

import pandas as pd

INTERIM = Path("data/interim")
PROCESSED = Path("data/processed")
ERAS = ["2010-2011", "2012-2023.2", "2023.4+"]
AMBIG = "애매"
CODES = {"missed": "SFNO", "over": "RCQ"}


def era_of(d):
    return "2010-2011" if d < "2012-01-01" else ("2012-2023.2" if d < "2023-03-01" else "2023.4+")


def ratio(a, b):
    return round(a / b, 4) if b else None


def agg(df):
    f = df[df["type"] == "flagged_vote"]
    c = df[df["type"] == "candidate_miss"]
    b = df[df["type"] == "boilerplate"]
    f_ok, f_over = (f.reviewer_judgment == "ok").sum(), (f.reviewer_judgment == "over").sum()
    c_bp = c[c["is_boilerplate"] == 1]
    c_nb = c[c["is_boilerplate"] == 0]
    m_all, m_nb = (c.reviewer_judgment == "missed").sum(), (c_nb.reviewer_judgment == "missed").sum()
    o_nb = (c_nb.reviewer_judgment == "ok").sum()
    amb = df["memo"].str.contains(AMBIG, regex=False)
    f_amb = f[f["memo"].str.contains(AMBIG, regex=False)]
    f_ok_x, f_over_x = f_ok - (f_amb.reviewer_judgment == "ok").sum(), f_over - (f_amb.reviewer_judgment == "over").sum()
    c_nb_x = c_nb[~c_nb["memo"].str.contains(AMBIG, regex=False)]
    m_nb_x = (c_nb_x.reviewer_judgment == "missed").sum()
    return {
        "n_docs": df["meeting_date"].nunique(),
        "flagged_n": len(f), "flagged_ok": f_ok, "flagged_over": f_over,
        "precision": ratio(f_ok, f_ok + f_over),
        "candidate_n": len(c), "candidate_boilerplate_rows": len(c_bp),
        "cand_ok_incl_bp": (c.reviewer_judgment == "ok").sum(), "cand_missed_incl_bp": m_all,
        "cand_ok_excl_bp": o_nb, "cand_missed_excl_bp": m_nb,
        "recall_upper_incl_bp": ratio(f_ok, f_ok + m_all),
        "recall_upper_excl_bp": ratio(f_ok, f_ok + m_nb),
        "boilerplate_ok": (b.reviewer_judgment == "ok").sum(), "boilerplate_over": (b.reviewer_judgment == "over").sum(),
        "ambiguous_rows": int(amb.sum()),
        "precision_excl_ambiguous": ratio(f_ok_x, f_ok_x + f_over_x),
        "recall_upper_excl_ambiguous": ratio(f_ok_x, f_ok_x + m_nb_x),
    }


def parse_codes(memo, kind):
    """Standalone code letters only: 'S', 'S/F', '[S]', 'S,N'. Returns [] when the memo has no code."""
    allowed = CODES[kind]
    toks = re.findall(r"(?<![A-Za-z가-힣])([A-Z])(?![A-Za-z가-힣])", memo or "")
    return [t for t in toks if t in allowed]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judged", default=str(INTERIM / "audit_votes_20_judged.csv"))
    ap.add_argument("--sentences", default=str(INTERIM / "sentences.csv"))
    ap.add_argument("--stance", default=str(INTERIM / "sentence_stance.csv"))
    ap.add_argument("--out", default=str(PROCESSED / "table_vote_audit.csv"))
    args = ap.parse_args()
    j = pd.read_csv(args.judged, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    s = pd.read_csv(args.sentences, encoding="utf-8-sig", dtype={"meeting_date": str})
    j = j.merge(s[["meeting_date", "sent_id", "is_boilerplate"]], on=["meeting_date", "sent_id"], how="left", validate="m:1")
    assert j["is_boilerplate"].notna().all()
    j["era"] = j["meeting_date"].map(era_of)

    rows = []
    for era in ERAS + ["all"]:
        sub = j if era == "all" else j[j["era"] == era]
        rows.append({"era": era, **agg(sub)})
    tab = pd.DataFrame(rows)
    PROCESSED.mkdir(exist_ok=True)
    tab.to_csv(args.out, index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print("== A2 audit table (recall_upper = flagged ok / (flagged ok + missed); candidate set = sentences containing 'Base Rate', "
          "so misses outside it are unobserved => UPPER bound) ==")
    print(tab.set_index("era").T.to_string())

    print("\n== A3 cause codes in memo ==")
    for kind, typ in [("missed", "candidate_miss"), ("over", "flagged_vote")]:
        sub = j[(j["type"] == typ) & (j["reviewer_judgment"] == kind)].copy()
        sub["codes"] = sub["memo"].map(lambda m: parse_codes(m, kind))
        coded = sub[sub["codes"].map(len) > 0]
        print(f"{kind}: {len(sub)} rows, {len(coded)} with a code, {len(sub) - len(coded)} without")
        if len(coded):
            print(coded.explode("codes").groupby(["codes", "era"]).size().to_string())
        for _, r in sub[(sub["memo"].str.strip() != "") & (sub["codes"].map(len) == 0)].iterrows():
            print(f"  memo without code {r['meeting_date']} #{r['sent_id']}: {r['memo']}")

    st = pd.read_csv(args.stance, encoding="utf-8-sig", dtype={"meeting_date": str})[["meeting_date", "sent_id", "pred_label"]]
    x = j[(j["is_boilerplate"] == 0) & (((j["type"] == "candidate_miss") & (j["reviewer_judgment"] == "missed"))
                                         | ((j["type"] == "flagged_vote") & (j["reviewer_judgment"] == "over")))].copy()
    x["kind"] = x["reviewer_judgment"]
    x = x.merge(st, on=["meeting_date", "sent_id"], how="left", validate="m:1")
    assert x["pred_label"].notna().all()
    eff = x.pivot_table(index=["meeting_date"], columns=["kind", "pred_label"], values="sent_id", aggfunc="count", fill_value=0)
    eff.columns = [f"{k}_{p}" for k, p in eff.columns]
    for k in ("missed", "over"):
        for p in ("hawkish", "dovish", "neutral", "irrelevant"):
            eff[f"{k}_{p}"] = eff.get(f"{k}_{p}", 0)
    cols = [f"{k}_{p}" for k in ("missed", "over") for p in ("hawkish", "dovish", "neutral", "irrelevant")]
    eff = eff.reindex(index=sorted(j["meeting_date"].unique()), fill_value=0)[cols].fillna(0).astype(int)
    eff["missed_in_index"] = eff["missed_hawkish"] + eff["missed_dovish"]  # missed votes that would enter the index as hawk/dove
    eff["over_removed_from_index"] = eff["over_hawkish"] + eff["over_dovish"]  # hawk/dove sentences lost by over-removal
    eff.to_csv(PROCESSED / "vote_audit_index_effect.csv", encoding="utf-8-sig")
    print("\n== A4 index effect by reviewed meeting (pred_label from sentence_stance.csv; no rate data used) ==")
    print(eff.to_string())
    print("total missed_in_index", int(eff["missed_in_index"].sum()), "| over_removed_from_index", int(eff["over_removed_from_index"].sum()))
    print("(missed rows with is_boilerplate=1 excluded:", int(((j["type"] == "candidate_miss") & (j["reviewer_judgment"] == "missed")
                                                              & (j["is_boilerplate"] == 1)).sum()), ")")


if __name__ == "__main__":
    main()
