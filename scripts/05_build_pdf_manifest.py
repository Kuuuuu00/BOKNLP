"""data/raw/pdf/*.pdf 의 매니페스트(pdf_manifest.csv)를 만들고 meeting_master.csv와 1:1 대응을 검사한다.

열: file_name, meeting_date(파일명에서), size_bytes, pages(pymupdf), sha256
불일치(누락·초과·날짜 형식 오류)가 있으면 종료코드 1로 멈춘다.

실행(저장소 루트에서): python scripts/05_build_pdf_manifest.py
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd
import pymupdf as fitz

ap = argparse.ArgumentParser()
ap.add_argument("--pdf", default="data/raw/pdf")
ap.add_argument("--master", default="data/metadata/meeting_master.csv")
ap.add_argument("--out", default="data/metadata/pdf_manifest.csv")
args = ap.parse_args()

rows, bad_names = [], []
for f in sorted(Path(args.pdf).glob("*.pdf")):
    hit = re.fullmatch(r"bok_minutes_(\d{4}-\d{2}-\d{2})\.pdf", f.name)
    if not hit:
        bad_names.append(f.name)
        continue
    with fitz.open(f) as doc:
        pages = len(doc)
    rows.append({"file_name": f.name, "meeting_date": hit.group(1), "size_bytes": f.stat().st_size,
                 "pages": pages, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})

man = pd.DataFrame(rows)
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
man.to_csv(args.out, index=False, encoding="utf-8-sig")

master = set(pd.read_csv(args.master, parse_dates=["meeting_date"])["meeting_date"].dt.strftime("%Y-%m-%d"))
files = list(man["meeting_date"])
dup = sorted({d for d in files if files.count(d) > 1})
missing = sorted(master - set(files))
extra = sorted(set(files) - master)

print(f"PDF {len(man)}개 / 마스터 {len(master)}건 → {args.out}")
print("파일명 형식 오류:", bad_names)
print("누락(마스터에만 있음):", missing)
print("초과(PDF에만 있음):", extra)
print("날짜 중복:", dup)
if bad_names or missing or extra or dup:
    sys.exit("불일치 있음 — 중단")
print("OK: 1:1 대응")
