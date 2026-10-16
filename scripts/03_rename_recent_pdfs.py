"""recent_pdf 폴더의 'Minutes of the Monetary Policy Board Meeting(August 2026).pdf' 형식 파일을
회의일 기준 이름 bok_minutes_YYYY-MM-DD.pdf 로 바꾼다(복사본 생성, 원본은 그대로 둠).

실행: python rename_recent_pdfs.py --src data/recent_pdf --dst data/pdf --master meeting_master.csv
"""
import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="data/raw/recent_pdf")
ap.add_argument("--dst", default="data/raw/pdf")
ap.add_argument("--master", default="data/metadata/meeting_master.csv")
args = ap.parse_args()

m = pd.read_csv(args.master, parse_dates=["meeting_date"])
m = m[m["in_wcb"] == 0]
by_month = {(d.year, d.month): d for d in m["meeting_date"]}  # 연 8회 체계: 한 달에 회의 1번

dst = Path(args.dst)
dst.mkdir(parents=True, exist_ok=True)
seen = set()
for f in sorted(Path(args.src).glob("*.pdf")):
    hit = re.search(r"\(([A-Za-z]+)\s+(\d{4})\)", f.name)
    if not hit:
        print("SKIP (월·연도 없음):", f.name)
        continue
    ym = pd.to_datetime(f"{hit.group(1)} {hit.group(2)}", format="%B %Y")
    d = by_month.get((ym.year, ym.month))
    if d is None:
        print("SKIP (마스터에 없는 달):", f.name)
        continue
    target = dst / f"bok_minutes_{d:%Y-%m-%d}.pdf"
    shutil.copy2(f, target)
    seen.add(d)
    print(f"{f.name}  ->  {target.name}")

missing = sorted(set(m["meeting_date"]) - seen)
print(f"\n복사 {len(seen)}건 / 마스터 기준 누락 {len(missing)}건:", [f"{x:%Y-%m-%d}" for x in missing])
