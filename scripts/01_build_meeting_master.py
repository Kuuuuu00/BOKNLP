"""WCB bank_of_korea_metadata.json → 회의 마스터 테이블(meeting_master.csv).

실행: python build_meeting_master.py --json data/raw_data/bank_of_korea/bank_of_korea_metadata.json
"""
import argparse
import json

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--json", default="data/raw/wcb/bank_of_korea_metadata.json")
ap.add_argument("--out", default="data/metadata/meeting_master.csv")
args = ap.parse_args()

# 1) WCB 메타데이터 (2010.1 ~ 2024.8, 147건). 날짜 형식은 DD-MM-YYYY
j = json.load(open(args.json, encoding="utf-8"))
d = pd.DataFrame([r for y in j for r in j[y]])
for c in ["release_date", "start_date", "end_date"]:
    d[c] = pd.to_datetime(d[c], format="%d-%m-%Y")
d = d.rename(columns={"start_date": "meeting_date", "release_date": "release_date_en",
                      "num_sentences": "wcb_num_sentences"})
d["in_wcb"] = 1
d["date_source"] = "WCB metadata"

# 2) WCB 범위 밖 회의 (BOK 홈페이지에서 직접 수집할 대상)
#    date_status: 'confirmed' = 보도로 확인, 'unverified' = BOK 일정표로 확인 필요
extra = [
    ("2024-10-11", "unverified"), ("2024-11-28", "unverified"),
    ("2025-01-16", "unverified"), ("2025-02-25", "confirmed"), ("2025-04-17", "unverified"),
    ("2025-05-29", "confirmed"), ("2025-07-10", "unverified"), ("2025-08-28", "unverified"),
    ("2025-10-23", "unverified"), ("2025-11-27", "confirmed"),
    ("2026-01-15", "confirmed"), ("2026-02-26", "confirmed"),
    (None, "TODO: 2026년 4월 회의일"), (None, "TODO: 2026년 5월 회의일"),
    ("2026-07-16", "confirmed"), ("2026-08-27", "confirmed"),
]
e = pd.DataFrame({"meeting_date": pd.to_datetime([x[0] for x in extra]),
                  "date_source": [x[1] for x in extra], "in_wcb": 0})
m = pd.concat([d, e], ignore_index=True).sort_values("meeting_date", na_position="last").reset_index(drop=True)

# 3) 플래그
EMERGENCY = {"2020-03-16"}  # 정례 일정 밖 회의
m["regular"] = (~m["meeting_date"].dt.strftime("%Y-%m-%d").isin(EMERGENCY)).astype(int)
m["freq_regime"] = ((m["meeting_date"].dt.year >= 2017) | m["meeting_date"].isna()).astype(int)  # D^freq: 연 8회 체계 (날짜 미정 행은 2026년)
m["in_main_sample"] = m["regular"]

# 4) 영문 의사록 게시 시차 (WCB release_date = BOK 영문 페이지 게시일로 추정)
m["lag_days"] = (m["release_date_en"] - m["meeting_date"]).dt.days
m["lag_bdays"] = [len(pd.bdate_range(s, r)) - 1 if pd.notna(r) else None
                  for s, r in zip(m["meeting_date"], m["release_date_en"])]
m["lag_regime"] = pd.cut(m["lag_days"], [0, 25, 40, 60, 200], labels=["~19d", "~33d", "~47d", "75d+"])

cols = ["meeting_date", "regular", "in_main_sample", "freq_regime", "in_wcb", "date_source",
        "release_date_en", "lag_days", "lag_bdays", "lag_regime", "wcb_num_sentences",
        "doc_id", "original_document_name", "cleaned_document_name", "minutes_link"]
m[cols].to_csv(args.out, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")

print(f"저장: {args.out}  (전체 {len(m)}행, WCB {m.in_wcb.sum()}건, 추가 수집 {(m.in_wcb == 0).sum()}건)")
print("연도별 회의 수:", m.groupby(m.meeting_date.dt.year).size().to_dict())
print(m.groupby("lag_regime", observed=True).agg(first=("meeting_date", "min"), last=("meeting_date", "max"),
                                                 n=("lag_days", "size"), median_days=("lag_days", "median")))
