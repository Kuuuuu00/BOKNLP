# BOKNLP

한국은행 금융통화위원회 영문 의사록(Minutes of the Monetary Policy Board Meeting) 연구용 데이터·코드 저장소.

## 폴더 구조

```
data/raw/pdf/            의사록 PDF 163개 (bok_minutes_YYYY-MM-DD.pdf, 읽기 전용)
data/raw/wcb/            WCB 산출물: final_data.csv, bank_of_korea_metadata.json (읽기 전용)
data/raw/wcb/cleaned_md/ 연도별 정제 md 147개 (읽기 전용)
data/metadata/           meeting_master.csv, raw_pdf_check.csv, pdf_manifest.csv
data/interim/            중간 산출물
data/processed/          분석용 최종 데이터
models/                  모델 가중치 (비어 있음, git 제외)
scripts/                 번호순 스크립트
```

`data/`와 `models/`는 git에서 제외된다(코드·문서만 커밋). 모든 명령은 저장소 루트에서 실행한다.

## 스크립트 (실행 순서)

| 번호 | 파일 | 역할 |
|---|---|---|
| 00 | `00_check_wcb_model.py` | WCB 스탠스 모델(`models/wcb_stance`)이 로드되고 final_data.csv 문장에서 동작하는지 점검. 모델 접근 승인 후 사용 |
| 01 | `01_build_meeting_master.py` | WCB 메타데이터 JSON + 추가 수집분으로 `meeting_master.csv` 생성 |
| 02 | (결번) | `download_wcb_pdfs.py`는 원본 폴더에 없어 복사하지 못함 |
| 03 | `03_rename_recent_pdfs.py` | 최근 PDF(`Minutes ...(Month YYYY).pdf`)를 회의일 기준 이름으로 복사 |
| 04 | `04_verify_raw_pdfs.py` | WCB PDF 147건을 마스터와 대조(파일명·누락·중복·무결성·내용 월) 후 복사 |
| 05 | `05_build_pdf_manifest.py` | `data/raw/pdf`의 크기·쪽수·SHA-256 매니페스트 작성, 마스터와 1:1 검사 |

01, 03, 04의 기본 경로는 새 구조에 맞췄지만, 이 저장소에는 원본 입력(`data/raw/recent_pdf`, 원래 WCB 파일명의 raw PDF)이 없어 그대로는 재실행되지 않는다. 03·04는 데이터 정리 때 한 번 실행한 이력용 스크립트다.

## 데이터 상태

- 회의 163회 = WCB 147건(2010-01~2024-08) + BOK 홈페이지 수동 수집 16건(2024-10~2026-08).
- `data/raw/pdf`의 PDF 163개는 `meeting_master.csv`와 1:1 대응(누락·초과 0, `pdf_manifest.csv`로 검증).
- 긴급회의 2020-03-16은 `regular=0`, `in_main_sample=0`이다. 나머지 162회는 정례회의.
