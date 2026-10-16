"""드라이브 이동 후 데이터 무결성을 검사한다.

1. pdf_manifest.csv 각 행: 파일 존재, 바이트 크기, SHA-256 대조
2. meeting_master.csv 와 PDF 파일명(bok_minutes_YYYY-MM-DD.pdf)이 1:1인지 확인
3. data/raw/wcb/final_data.csv 가 1,000행이고 Git LFS 포인터가 아닌지 확인
불일치가 하나라도 있으면 목록을 출력하고 종료코드 1.

실행(저장소 루트에서): python scripts/07_verify_manifest.py
"""
import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--pdf", default="data/raw/pdf")
ap.add_argument("--manifest", default="data/metadata/pdf_manifest.csv")
ap.add_argument("--master", default="data/metadata/meeting_master.csv")
ap.add_argument("--wcb", default="data/raw/wcb/final_data.csv")
ap.add_argument("--wcb-rows", type=int, default=1000)
args = ap.parse_args()

problems = []
pdf_dir = Path(args.pdf)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# 1. 매니페스트 대조
with open(args.manifest, encoding="utf-8-sig", newline="") as f:
    manifest = list(csv.DictReader(f))
for r in manifest:
    p = pdf_dir / r["file_name"]
    if not p.is_file():
        problems.append(f"[manifest] 파일 없음: {r['file_name']}")
        continue
    size = p.stat().st_size
    if size != int(r["size_bytes"]):
        problems.append(f"[manifest] 크기 불일치: {r['file_name']} ({size} != {r['size_bytes']})")
    digest = sha256(p)
    if digest != r["sha256"]:
        problems.append(f"[manifest] SHA-256 불일치: {r['file_name']}")

# 2. meeting_master <-> PDF 1:1
with open(args.master, encoding="utf-8-sig", newline="") as f:
    master_dates = [r["meeting_date"] for r in csv.DictReader(f)]
expected = {f"bok_minutes_{d}.pdf" for d in master_dates}
actual = {p.name for p in pdf_dir.glob("*.pdf")}
if len(master_dates) != len(expected):
    problems.append("[master] meeting_date 중복이 있음")
for n in sorted(expected - actual):
    problems.append(f"[master] PDF 누락: {n}")
for n in sorted(actual - expected):
    problems.append(f"[master] master에 없는 PDF: {n}")
for n in sorted(actual):
    if not re.fullmatch(r"bok_minutes_\d{4}-\d{2}-\d{2}\.pdf", n):
        problems.append(f"[master] 파일명 형식 오류: {n}")
manifest_names = {r["file_name"] for r in manifest}
for n in sorted(actual ^ manifest_names):
    problems.append(f"[manifest] manifest와 디렉터리 불일치: {n}")

# 3. WCB final_data.csv
wcb = Path(args.wcb)
if not wcb.is_file():
    problems.append(f"[wcb] 파일 없음: {wcb}")
else:
    with open(wcb, "rb") as f:
        head = f.read(200)
    if head.startswith(b"version https://git-lfs"):
        problems.append("[wcb] Git LFS 포인터 파일임 (실제 데이터 아님)")
    else:
        with open(wcb, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.reader(f)) - 1
        if n != args.wcb_rows:
            problems.append(f"[wcb] 행 수 {n} != {args.wcb_rows}")

print(f"PDF {len(actual)}개, manifest {len(manifest)}행, master {len(master_dates)}행")
if problems:
    print(f"불일치 {len(problems)}건:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("OK: 모든 무결성 검사 통과")
