"""PDF 구조 진단: 섹션 추출 규칙 설계용 (추출 로직을 확정하지 않는다).

163개 PDF에서 앵커 문구 위치, 로마숫자 섹션 제목, 반복 머리글·꼬리말, 각주 패턴을 기록한다.
출력: data/interim/structure_report.csv, data/interim/samples/bok_minutes_YYYY-MM-DD.txt

실행(저장소 루트에서): uv run --with pymupdf --with pandas python scripts/08_inspect_pdf_structure.py
"""
import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import pymupdf as fitz

ap = argparse.ArgumentParser()
ap.add_argument("--pdf", default="data/raw/pdf")
ap.add_argument("--out", default="data/interim/structure_report.csv")
ap.add_argument("--samples", default="data/interim/samples")
args = ap.parse_args()

SAMPLE_DATES = ["2010-12-09", "2013-05-09", "2017-11-30", "2020-05-28", "2026-08-27"]

START = {
    "s_heading": r"discussion related to monetary policy decision",
    "s_discuss": r"discussions? (on|concerning|related to)",
    "s_on_changes": r"discussions on changes in the bank of korea base rate were as follows",
    "s_concerning": r"discussions concerning a change in the bank of korea base rate were as follows",
}
END = {
    "e_after": r"after the discussions detailed above",
    "e_ref": r"< ?ref ?>",
    "e_mpd": r"monetary policy decision",  # START 이후 처음 나오는 곳 (아래에서 처리)
    "e_govrep": r"remarks by (the )?government representative",
    "e_delib": r"results of (the )?deliberation",
    "e_minority": r"minority opinion",
}
ROMAN = r"(?:[ⅠⅡⅢⅣⅤⅥ]|VI|IV|V|I{1,3})"
ROMAN_RE = re.compile(rf"^\s*({ROMAN})(?:\s*\.\s*|\s+)(\S.{{0,80}})$")
FOOT_PATTERNS = {
    "fn_paren": re.compile(r"(?<![\d.,])\b\d{1,2}\)"),
    "fn_bracket": re.compile(r"\[\d{1,2}\)?\]"),
    "fn_super": re.compile(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]"),
}


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def build_norm(pages):
    """쪽별 정규화 텍스트를 이어 붙이고 각 쪽 시작 오프셋을 반환."""
    parts, offsets, pos = [], [], 0
    for t in pages:
        n = norm(t)
        offsets.append(pos)
        parts.append(n)
        pos += len(n) + 1
    return " ".join(parts), offsets


def page_of(offsets, pos):
    p = 0
    for i, o in enumerate(offsets):
        if o <= pos:
            p = i
    return p + 1


def first_hit(rx, text, offsets, start=0):
    m = re.compile(rx).search(text, start)
    return (page_of(offsets, m.start()), m.start()) if m else (None, None)


def header_footer_candidates(pages):
    """3쪽 이상에서 (숫자를 #으로 바꿔) 반복되는, 쪽의 앞·뒤 3줄 후보."""
    cnt = Counter()
    for t in pages:
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        edge = set(re.sub(r"\d+", "#", l) for l in lines[:3] + lines[-3:])
        cnt.update(edge)
    return [f"{l} (x{c})" for l, c in cnt.most_common(6) if c >= 3]


rows = []
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.samples).mkdir(parents=True, exist_ok=True)

for f in sorted(Path(args.pdf).glob("bok_minutes_*.pdf")):
    date = f.stem.replace("bok_minutes_", "")
    with fitz.open(f) as doc:
        pages = [p.get_text() for p in doc]
    text, offs = build_norm(pages)
    row = {"meeting_date": date, "n_pages": len(pages), "n_chars": sum(len(p) for p in pages)}

    start_pos = None
    for k, rx in START.items():
        pg, pos = first_hit(rx, text, offs)
        row[k + "_page"] = pg
        if k != "s_discuss" and pos is not None:
            start_pos = pos if start_pos is None else min(start_pos, pos)
    # "Monetary Policy Decision" 은 START 후보 첫 위치 이후에서만 찾는다
    for k, rx in END.items():
        if k == "e_mpd":
            if start_pos is None:
                pg, pos = None, None
            else:
                pg, pos = first_hit(rx, text, offs, start_pos + 1)
                # START 헤딩 자체("discussion related to monetary policy decision")는 건너뛴다
                while pos is not None and text[max(0, pos - 20):pos].endswith("related to "):
                    pg, pos = first_hit(rx, text, offs, pos + 1)
        else:
            pg, pos = first_hit(rx, text, offs)
        row[k + "_page"] = pg
    row["any_start"] = int(any(row[k + "_page"] for k in START))
    row["any_end"] = int(any(row[k + "_page"] for k in END))

    heads = []
    for t in pages:
        for line in t.splitlines():
            m = ROMAN_RE.match(line)
            if m:
                heads.append(f"{m.group(1)}:{m.group(2).strip()[:50]}")
    row["roman_headings"] = " | ".join(heads)
    row["roman_seq"] = "".join(h.split(":")[0] + "," for h in heads)
    row["header_footer"] = " || ".join(header_footer_candidates(pages))

    full = "\n".join(pages)
    for k, rx in FOOT_PATTERNS.items():
        row[k] = len(rx.findall(full))
    rows.append(row)

    if date in SAMPLE_DATES:
        out = Path(args.samples) / f"bok_minutes_{date}.txt"
        out.write_text("".join(f"=== PAGE {i} ===\n{t}\n" for i, t in enumerate(pages, 1)),
                       encoding="utf-8")

df = pd.DataFrame(rows)
df.to_csv(args.out, index=False, encoding="utf-8-sig")
print(f"{len(df)}개 문서 -> {args.out}")
