"""P2: build the human review workbook from audit_votes_20.csv (guide C2/C3/C4).
uv run python scripts/10b_make_vote_review_xlsx.py
Adds prev_sent / next_sent (same meeting only). Judgment is filled in the workbook, then merged by 10c_merge_vote_review.py.
"""
import argparse
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

INTERIM = Path("data/interim")
ALLOWED = {"flagged_vote": "ok,over", "candidate_miss": "ok,missed", "boilerplate": "ok,over"}
COLS = ["meeting_date", "sent_id", "type", "prev_sent", "sent_raw", "next_sent", "is_vote", "vote_rule", "reviewer_judgment", "memo"]
WIDTH = {"meeting_date": 12, "sent_id": 8, "type": 15, "prev_sent": 55, "sent_raw": 80, "next_sent": 55, "is_vote": 8, "vote_rule": 26, "reviewer_judgment": 16, "memo": 30}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default=str(INTERIM / "audit_votes_20.csv"))
    ap.add_argument("--sentences", default=str(INTERIM / "sentences.csv"))
    ap.add_argument("--out", default=str(INTERIM / "audit_votes_20_review.xlsx"))
    args = ap.parse_args()
    av = pd.read_csv(args.audit, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    sent = pd.read_csv(args.sentences, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    txt = {(r.meeting_date, r.sent_id): r.sent_raw for r in sent.itertuples()}
    av["prev_sent"] = [txt.get((d, i - 1), "") for d, i in zip(av.meeting_date, av.sent_id)]
    av["next_sent"] = [txt.get((d, i + 1), "") for d, i in zip(av.meeting_date, av.sent_id)]
    av = av.sort_values(["meeting_date", "sent_id"], kind="stable")[COLS]
    wb = Workbook()
    ws = wb.active
    ws.title = "review"
    ws.append(COLS)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for r in av.itertuples(index=False):
        ws.append(list(r))
    for row in ws.iter_rows(min_row=2):
        row[0].number_format = "@"
        row[0].value = str(row[0].value)
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, name in enumerate(COLS, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = WIDTH[name]
    ws.freeze_panes = "A2"
    jcol = ws.cell(1, COLS.index("reviewer_judgment") + 1).column_letter
    for typ, allowed in ALLOWED.items():
        dv = DataValidation(type="list", formula1=f'"{allowed}"', allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(dv)
        for r in range(2, ws.max_row + 1):
            if ws.cell(r, 3).value == typ:
                dv.add(f"{jcol}{r}")
    wb.save(args.out)
    print(args.out, len(av), av["type"].value_counts().to_dict())


if __name__ == "__main__":
    main()
