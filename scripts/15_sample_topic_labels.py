"""P5-0 / P5-b: draw the human topic-label samples (guide A). Only --kind dev is implemented now.
uv run python scripts/15_sample_topic_labels.py --kind dev --n 40 --seed 20261106
Corpus = sentences with is_vote=0 and is_boilerplate=0 (v1.3 flags). Era-stratified, proportional to eligible sentences (largest remainder, >=1
per era), seeded. Sentences identical to a guide A4 example are excluded. The drawn (meeting_date, sent_id) keys are saved to
topic_dev_sample_ids.csv and MUST be excluded from the later validation sample: use excluded_keys() / eligible_for_validation().
The review workbook shows NO model stance and NO LLM topic. Sheet 2 copies guide A1-A3 verbatim from docs/annotation_guide.md.
"""
import argparse
import json
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

INTERIM = Path("data/interim")
GUIDE = Path("docs/annotation_guide.md")
KEY = ["meeting_date", "sent_id"]  # sent_id restarts in every meeting
TOPICS = ("Macro", "FinStab", "External", "Other")
AMBIGUOUS = ("0", "1")
ERAS = ["2010-2011", "2012-2023.2", "2023.4+"]
DEV_IDS = INTERIM / "topic_dev_sample_ids.csv"


def era_of(d):
    return "2010-2011" if d < "2012-01-01" else ("2012-2023.2" if d < "2023-03-01" else "2023.4+")


def norm(s):
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def a4_example_texts(guide=GUIDE):
    """Sentences of the guide A4 example table (excluded from every human sample, plan 1.1b)."""
    txt = guide.read_text(encoding="utf-8")
    sec = txt.split("## A4.", 1)[1].split("\n---", 1)[0]
    out = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0].isdigit():
            out.append(norm(cells[1]))
    return out


def eligible(sent):
    """Corpus sentences that enter the index: not a vote sentence, not boilerplate."""
    return sent[(sent["is_vote"] == 0) & (sent["is_boilerplate"] == 0)]


def excluded_keys(dev_ids=DEV_IDS):
    """Keys that must never appear in the validation sample (the 40 development sentences)."""
    if not Path(dev_ids).exists():
        return set()
    d = pd.read_csv(dev_ids, dtype={"meeting_date": str})
    return set(zip(d["meeting_date"], d["sent_id"].astype(int)))


def eligible_for_validation(sent, dev_ids=DEV_IDS):
    """Pool for the 120-sentence validation sample: eligible, not an A4 example, not in the development sample."""
    pool = eligible(sent)
    ex = excluded_keys(dev_ids)
    a4 = set(a4_example_texts())
    keep = [(k not in ex) and (norm(t) not in a4) for k, t in zip(zip(pool["meeting_date"], pool["sent_id"].astype(int)), pool["sent_raw"])]
    return pool[keep]


def allocate(counts, n):
    share = counts / counts.sum() * n
    base = share.apply(int).clip(lower=1)
    while base.sum() > n:
        base[base.idxmax()] -= 1
    rem = (share - base).sort_values(ascending=False)
    for e in rem.index:
        if base.sum() >= n:
            break
        base[e] += 1
    return base


def guide_a_rows():
    """Guide A1-A3 verbatim (markdown lines; table lines split into cells)."""
    txt = GUIDE.read_text(encoding="utf-8")
    sec = "## A1." + txt.split("## A1.", 1)[1].split("## A4.", 1)[0]
    rows = []
    for line in sec.splitlines():
        if not line.strip():
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append(("table", cells))
        else:
            rows.append(("text", [line.rstrip()]))
    return rows, re.search(r"가이드 (v[\d.]+)", txt).group(1)


def write_workbook(df, path):
    wb = Workbook()
    ws = wb.active
    ws.title = "label"
    cols = ["meeting_date", "sent_id", "prev_sent", "sent_raw", "next_sent", "human_topic", "ambiguous", "memo"]
    widths = [12, 8, 55, 80, 55, 14, 10, 40]
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for r in df[cols].itertuples(index=False):
        ws.append(["" if v is None else v for v in r])
    for row in ws.iter_rows(min_row=2):
        row[0].number_format = "@"
        row[0].value = str(row[0].value)
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = "A2"
    for col, allowed in (("F", TOPICS), ("G", AMBIGUOUS)):
        dv = DataValidation(type="list", formula1='"' + ",".join(allowed) + '"', allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{ws.max_row}")
    g = wb.create_sheet("guide A")
    rows, ver = guide_a_rows()
    g.append([f"주석 가이드 {ver} A1~A3 원문 (docs/annotation_guide.md에서 그대로 복사)"])
    g["A1"].font = Font(bold=True)
    for kind, cells in rows:
        g.append(cells)
        if kind == "text" and cells[0].startswith("#"):
            g.cell(g.max_row, 1).font = Font(bold=True)
    g.column_dimensions["A"].width = 50
    g.column_dimensions["B"].width = 70
    g.column_dimensions["C"].width = 60
    for row in g.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["dev", "val"], required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--sentences", default=str(INTERIM / "sentences.csv"))
    ap.add_argument("--out", default=str(INTERIM / "topic_dev_sample.csv"))
    ap.add_argument("--xlsx", default=str(INTERIM / "topic_dev_review.xlsx"))
    args = ap.parse_args()
    if args.kind == "val":
        raise SystemExit("--kind val needs sentence_topic.csv from P5-a (LLM topics, 30 per topic); not implemented yet. "
                         "Use eligible_for_validation() so the development sample and A4 examples stay excluded.")
    if Path(args.out).exists() and Path(DEV_IDS).exists():
        raise SystemExit(f"{DEV_IDS} already exists: the development sample is frozen. Delete it deliberately to redraw.")
    sent = pd.read_csv(args.sentences, encoding="utf-8-sig", dtype={"meeting_date": str})
    sent["era"] = sent["meeting_date"].map(era_of)
    pool = eligible(sent)
    a4 = set(a4_example_texts())
    hit = pool[pool["sent_raw"].map(norm).isin(a4)]
    pool = pool.drop(hit.index)
    counts = pool["era"].value_counts().reindex(ERAS)
    alloc = allocate(counts, args.n)
    pick = pd.concat([pool[pool["era"] == e].sample(int(alloc[e]), random_state=args.seed) for e in ERAS])
    pick = pick.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    txt = {(r.meeting_date, r.sent_id): r.sent_raw for r in sent.itertuples()}
    pick["prev_sent"] = [txt.get((d, i - 1), "") for d, i in zip(pick.meeting_date, pick.sent_id)]
    pick["next_sent"] = [txt.get((d, i + 1), "") for d, i in zip(pick.meeting_date, pick.sent_id)]
    pick["human_topic"], pick["ambiguous"], pick["memo"] = "", "", ""
    pick[KEY + ["era"]].to_csv(DEV_IDS, index=False)
    pick[KEY + ["sent_raw", "human_topic", "ambiguous", "memo"]].to_csv(args.out, index=False, encoding="utf-8-sig")
    write_workbook(pick, args.xlsx)
    meta = {"kind": args.kind, "n": args.n, "seed": args.seed, "pool_size": int(len(pool)), "pool_by_era": counts.to_dict(),
            "alloc_by_era": {e: int(alloc[e]) for e in ERAS}, "a4_examples": len(a4), "a4_matches_removed": int(len(hit)),
            "corpus_filter": "is_vote==0 & is_boilerplate==0 (v1.3 flags)"}
    Path(args.out).with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print("excluded_keys() size:", len(excluded_keys()), "| eligible_for_validation pool:", len(eligible_for_validation(sent)))


if __name__ == "__main__":
    main()
