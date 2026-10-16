"""raw_data의 WCB PDF 147건을 마스터 테이블과 대조하고, 통과한 파일을 data/pdf/bok_minutes_YYYY-MM-DD.pdf로 복사한다.

점검 항목
  1) 파일명 대응: 마스터의 original_document_name(bank_of_korea_DD-MM-YYYY.pdf)과 일치하는지
  2) 누락·중복: 마스터 147건 중 파일이 없는 회의, 같은 회의에 파일이 2개 이상인 경우
  3) 파일 무결성: 진짜 PDF인지(%PDF 헤더), Git LFS 포인터가 아닌지
  4) 내용 대응: PDF 앞 2쪽에 회의 '월 연도'(예: December 2010)가 나오는지

실행:
  pip install pymupdf pandas
  python verify_raw_pdfs.py --raw data/raw_data/bank_of_korea --master data/metadata/meeting_master.csv --dst data/pdf
결과: data/metadata/raw_pdf_check.csv (행마다 점검 결과), 콘솔 요약
"""
import argparse
import re
import shutil
from pathlib import Path

import pymupdf as fitz
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default="data/raw/pdf")
ap.add_argument("--master", default="data/metadata/meeting_master.csv")
ap.add_argument("--dst", default="data/raw/pdf")
ap.add_argument("--report", default="data/metadata/raw_pdf_check.csv")
ap.add_argument("--no-copy", action="store_true", help="점검만 하고 복사하지 않음")
args = ap.parse_args()

m = pd.read_csv(args.master, parse_dates=["meeting_date"])
m = m[m["in_wcb"] == 1].copy()

files = sorted(Path(args.raw).rglob("*.pdf"))
by_name = {}
for f in files:
    by_name.setdefault(f.name, []).append(f)

# 마스터에 없는 파일(예상 밖 파일)
expected = set(m["original_document_name"])
unexpected = [f for f in files if f.name not in expected]


def month_year_on_first_pages(path, n_pages=2):
    with fitz.open(path) as doc:
        text = " ".join(doc[i].get_text() for i in range(min(n_pages, len(doc))))
        n = len(doc)
    text = re.sub(r"\s+", " ", text)
    found = set()
    for mon, yr in re.findall(r"(January|February|March|April|May|June|July|August|September|"
                              r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
                              r"\.?\s+(?:\d{1,2},?\s+)?(\d{4})", text):
        try:
            found.add(pd.to_datetime(f"{mon[:3]} {yr}", format="%b %Y").strftime("%Y-%m"))
        except ValueError:
            pass
    return found, n


rows = []
dst = Path(args.dst)
if not args.no_copy:
    dst.mkdir(parents=True, exist_ok=True)

for _, r in m.iterrows():
    hits = by_name.get(r.original_document_name, [])
    row = {"meeting_date": r.meeting_date.date(), "expected_file": r.original_document_name,
           "n_files": len(hits), "path": str(hits[0]) if hits else "", "is_pdf": None,
           "pages": None, "month_match": None, "months_found": "", "copied": False}
    if len(hits) == 1:
        f = hits[0]
        head = f.read_bytes()[:200]
        row["is_pdf"] = head.startswith(b"%PDF")
        if b"git-lfs" in head:
            row["is_pdf"] = False
        if row["is_pdf"]:
            found, n = month_year_on_first_pages(f)
            row["pages"] = n
            row["months_found"] = ";".join(sorted(found))
            row["month_match"] = r.meeting_date.strftime("%Y-%m") in found
            if not args.no_copy:
                shutil.copy2(f, dst / f"bok_minutes_{r.meeting_date:%Y-%m-%d}.pdf")
                row["copied"] = True
    rows.append(row)

rep = pd.DataFrame(rows)
Path(args.report).parent.mkdir(parents=True, exist_ok=True)
rep.to_csv(args.report, index=False, encoding="utf-8-sig")

print(f"raw PDF {len(files)}개 / 마스터(WCB) {len(m)}건")
miss = rep.loc[rep.n_files == 0, "meeting_date"].astype(str).tolist()
print(f"누락(파일 없음) {len(miss)}건:", miss[:20], "..." if len(miss) > 20 else "")
print("중복(파일 2개 이상):", rep.loc[rep.n_files > 1, "meeting_date"].astype(str).tolist())
print("마스터에 없는 파일:", [f.name for f in unexpected])
print("PDF 아님/LFS 포인터:", rep.loc[rep.is_pdf == False, "meeting_date"].astype(str).tolist())  # noqa: E712
mis = rep[rep.month_match == False]  # noqa: E712
print(f"앞 2쪽에 회의 월이 안 보임: {len(mis)}건 → 직접 확인")
if len(mis):
    print(mis[["meeting_date", "expected_file", "months_found"]].to_string(index=False))
print(f"복사: {int(rep.copied.sum())}건 → {dst}   (data/pdf 총 {len(list(dst.glob('*.pdf')))}개, 163이면 완료)")
print("보고서:", args.report)
