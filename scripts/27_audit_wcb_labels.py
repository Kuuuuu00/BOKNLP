"""P3: candidate extraction and blind review workbook for the WCB label-direction audit (guide B, proposal 5.3).
Plan number 11_audit_wcb_labels.py -> actual file 27_ (see the number table in plan.md).
uv run python scripts/27_audit_wcb_labels.py
Reads data/raw/wcb/final_data.csv only. Writes (data/interim): wcb_label_audit_candidates.csv, wcb_label_audit.csv (empty template),
wcb_label_audit_keyword_hits.csv, wcb_label_audit_review.xlsx.
Judgments (row_type, expected_direction, judgment, memo) are NEVER pre-filled. The WCB label sits on a separate sheet so that
expected_direction can be recorded without seeing it (guide B2).
"""
import argparse
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

INTERIM = Path("data/interim")

# category -> (expected_topic, {keyword label: regex}); matched on the lowercased sentence
KEYWORDS = {
    "fx": ("External", {
        "won": r"(?<!trillion )(?<!billion )(?<!million )(?<!trillion-)(?<!billion-)(?<!million-)\bwon\b",
        "exchange rate": r"exchange rate", "foreign exchange": r"foreign exchange|\bfx\b|foreign-exchange",
        "currency": r"\bcurrenc(?:y|ies)\b", "depreciat*": r"depreciat", "appreciat*": r"appreciat",
        "capital flow": r"capital (?:outflow|inflow|flow|movement)s?|(?:outflow|inflow)s? of (?:foreign )?capital|foreign capital|global capital",
        "dollar": r"\bdollar\b",
        "foreign portfolio": r"foreign (?:portfolio|investors?|funds?|inflows?)|foreigners?|portfolio (?:investment|inflow|outflow)s?",
    }),
    "external_rates": ("External", {
        "fed": r"\bfed\b|federal reserve|federal funds|\bfomc\b", "rate differential": r"(?:interest )?rate (?:differential|gap|spread)|differential",
        "us rates": r"\bu\.?s\.? (?:interest|monetary|policy|rate|treasury)", "tapering": r"taper",
        "major-country policy": r"(?:\bus\b|u\.s\.|major countr\w+|advanced countr\w+).{0,40}(?:rate hikes?|rate cuts?|monetary polic\w+)|diverging monetary polic\w+|\becb\b|european central bank|bank of japan",
        "intl fin market volatility": r"(?:international|global) financial market (?:volatil\w*|unrest|instability)|financial market unrest|price variables",
        "external soundness": r"external debt|foreign (?:exchange )?reserves?|current account|currency swap|swap line",
    }),
    "housing": ("FinStab", {
        "housing": r"\bhousing\b(?! (?:construction|services?\b))|\bhome (?:price|sales|loan)",
        "house price": r"house price|home price|apartment price|real[- ]estate|property price|leasehold|jeonse|chonsei",
    }),
    "household_debt": ("FinStab", {
        "household debt": r"household (?:debt|loan|credit|lending|leverage)|mortgage|debt-to-income|\bltv\b|\bdti\b|\bdsr\b|household and corporate (?:loan|lend\w+|debt)",
        "leverage": r"leverag|risk[- ]taking|search for yield",
        "financial imbalances": r"financial imbalance",
        "repayment burden": r"(?:debt|loan)[- ]?(?:servicing|repayment)s?(?: burden)?|principal and interest|repayment burden",
    }),
    "credit": ("FinStab", {
        "delinquen*": r"delinquen", "default": r"\bdefault", "credit crunch": r"credit crunch|credit crisis|credit squeeze",
        "insolvency": r"insolven|bankruptc|\bnpl\b|non-performing", "project financing": r"project financing|\bpf\b|real estate pf",
        "liquidity stress": r"liquidity (?:stress|risk|shortage|crunch)", "non-bank": r"non-?bank",
        "credit spread/risk": r"credit (?:spread|risk)s?", "asset prices": r"asset prices?",
    }),
}
EXCLUDE = re.compile(r"fx and international finance")  # agenda-list boilerplate, no content
COLS = ["row_id", "year", "sentences", "keyword_hits", "expected_topic", "row_type", "expected_direction", "judgment", "memo"]
WIDTH = {"row_id": 8, "year": 7, "sentences": 90, "keyword_hits": 28, "expected_topic": 18, "row_type": 14, "expected_direction": 18, "judgment": 12, "memo": 30}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/raw/wcb/final_data.csv")
    ap.add_argument("--outdir", default=str(INTERIM))
    args = ap.parse_args()
    out = Path(args.outdir)
    df = pd.read_csv(args.inp, encoding="utf-8-sig")
    df["row_id"] = range(len(df))  # 0-based row number of final_data.csv
    low = df["sentences"].astype(str).str.lower()
    hits, topics, hit_rows = [], [], []
    for rid, t in zip(df["row_id"], low):
        h, tp = [], set()
        if EXCLUDE.search(t):
            hits.append("")
            topics.append("")
            continue
        for cat, (topic, kws) in KEYWORDS.items():
            for lab, rx in kws.items():
                if re.search(rx, t):
                    h.append(f"{cat}:{lab}")
                    tp.add(topic)
                    hit_rows.append({"row_id": rid, "category": cat, "keyword": lab})
        hits.append("; ".join(h))
        topics.append("|".join(sorted(tp)))
    df["keyword_hits"], df["expected_topic"] = hits, topics
    cand = df[df["keyword_hits"] != ""][["row_id", "year", "sentences", "stance_label", "keyword_hits", "expected_topic"]]
    cand.to_csv(out / "wcb_label_audit_candidates.csv", index=False, encoding="utf-8-sig")
    hr = pd.DataFrame(hit_rows)
    kh = hr.groupby(["category", "keyword"]).agg(n_rows=("row_id", "nunique")).reset_index()
    kh.to_csv(out / "wcb_label_audit_keyword_hits.csv", index=False, encoding="utf-8-sig")
    tmpl = cand.copy()
    for c in ["row_type", "expected_direction", "judgment", "memo"]:
        tmpl[c] = ""
    tmpl.to_csv(out / "wcb_label_audit.csv", index=False, encoding="utf-8-sig")
    make_xlsx(cand, out / "wcb_label_audit_review.xlsx")
    print("rows", len(df), "candidates", len(cand))
    print(cand["expected_topic"].value_counts().to_string())
    print(kh.to_string(index=False))


def make_xlsx(cand, path):
    wb = Workbook()
    ws = wb.active
    ws.title = "review"
    ws.append(COLS)
    for r in cand.itertuples(index=False):
        ws.append([r.row_id, r.year, r.sentences, r.keyword_hits, r.expected_topic, None, None, None, None])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, name in enumerate(COLS, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = WIDTH[name]
    ws.freeze_panes = "A2"
    n = ws.max_row
    for name, allowed in [("row_type", "orig,symmetric"), ("expected_direction", "hawkish,dovish"), ("judgment", "일치,애매,불일치,대상아님")]:
        col = ws.cell(1, COLS.index(name) + 1).column_letter
        dv = DataValidation(type="list", formula1=f'"{allowed}"', allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    ws2 = wb.create_sheet("wcb_label")
    ws2.append(["row_id", "stance_label"])
    for r in cand.itertuples(index=False):
        ws2.append([r.row_id, r.stance_label])
    for c in ws2[1]:
        c.font = Font(bold=True)
    ws2.freeze_panes = "A2"
    wb.save(path)


if __name__ == "__main__":
    main()
