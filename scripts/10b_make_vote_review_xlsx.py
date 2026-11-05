"""P2: build the human review workbook from audit_votes_20.csv (guide C2/C3/C4).
uv run python scripts/10b_make_vote_review_xlsx.py
Adds prev_sent / next_sent (same meeting only). Judgment is filled in the workbook, then merged by 10c_merge_vote_review.py.
"""
import argparse
import shutil
import time
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from vote_review_common import ALLOWED

INTERIM = Path("data/interim")
COLS = ["meeting_date", "sent_id", "type", "prev_sent", "sent_raw", "next_sent", "is_vote", "vote_rule", "is_boilerplate", "boilerplate_rule", "reviewer_judgment", "memo"]
WIDTH = {"meeting_date": 12, "sent_id": 8, "type": 15, "prev_sent": 55, "sent_raw": 80, "next_sent": 55, "is_vote": 8, "vote_rule": 26, "is_boilerplate": 12, "boilerplate_rule": 26, "reviewer_judgment": 16, "memo": 30}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default=str(INTERIM / "audit_votes_20.csv"))
    ap.add_argument("--sentences", default=str(INTERIM / "sentences.csv"))
    ap.add_argument("--out", default=str(INTERIM / "audit_votes_20_review.xlsx"))
    args = ap.parse_args()
    av = pd.read_csv(args.audit, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    sent = pd.read_csv(args.sentences, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    txt = {(r.meeting_date, r.sent_id): r.sent_raw for r in sent.itertuples()}
    bp = sent.set_index(["meeting_date", "sent_id"])[["is_boilerplate", "boilerplate_rule"]]
    av = av.join(bp, on=["meeting_date", "sent_id"])
    av["prev_sent"] = [txt.get((d, i - 1), "") for d, i in zip(av.meeting_date, av.sent_id)]
    av["next_sent"] = [txt.get((d, i + 1), "") for d, i in zip(av.meeting_date, av.sent_id)]
    av = av.sort_values(["meeting_date", "sent_id", "type"], kind="stable")[COLS]
    kept = {}
    out_path = Path(args.out)
    if out_path.exists():  # carry over judgments typed into the previous workbook, keyed by (meeting_date, sent_id, type)
        bdir = INTERIM / "_backup"
        bdir.mkdir(exist_ok=True)
        shutil.copy2(out_path, bdir / f"{out_path.stem}_{time.strftime('%Y%m%d_%H%M%S')}{out_path.suffix}")
        old = load_workbook(out_path).active
        hdr = [c.value for c in old[1]]
        for r in old.iter_rows(min_row=2, values_only=True):
            d = dict(zip(hdr, r))
            if d.get("reviewer_judgment") or d.get("memo"):
                kept[(str(d["meeting_date"]), int(d["sent_id"]), d["type"])] = (d.get("reviewer_judgment") or "", d.get("memo") or "")
    keys = list(zip(av.meeting_date, av.sent_id, av.type))
    rows_per_sent = av.groupby(["meeting_date", "sent_id"]).size().to_dict()
    moved = {}  # old type no longer matches the audit file: carry by (meeting_date, sent_id) only if that sentence has a single row
    for k in list(kept):
        if k not in keys and rows_per_sent.get((k[0], k[1])) == 1:
            new_k = next(x for x in keys if x[:2] == k[:2])
            moved[k] = new_k
            kept[new_k] = kept.pop(k)
    av["reviewer_judgment"] = [kept.get(k, ("", ""))[0] for k in keys]
    av["memo"] = [kept.get(k, ("", ""))[1] for k in keys]
    invalid = [(k, v[0]) for k, v in kept.items() if v[0] and k in keys and v[0] not in ALLOWED[k[2]]]
    lost = [k for k in kept if k not in set(keys)]
    wb = Workbook()
    ws = wb.active
    ws.title = "review"
    ws.append(COLS)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for r in av.itertuples(index=False):
        ws.append(["" if v is None else v for v in r])
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
        dv = DataValidation(type="list", formula1='"' + ",".join(allowed) + '"', allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(dv)
        for r in range(2, ws.max_row + 1):
            if ws.cell(r, 3).value == typ:
                dv.add(f"{jcol}{r}")
    wb.save(args.out)
    print(args.out, len(av), av["type"].value_counts().to_dict())
    print("preserved judgments/memos:", len(kept), "| not found in new workbook:", lost)
    print("carried over under a different type (old key -> new key):", moved)
    print("values outside the allowed set (kept as typed):", invalid)


if __name__ == "__main__":
    main()
