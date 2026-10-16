# 데이터 출처

## WCB 레포지토리
- https://github.com/gtfintechlab/WorldCentralBanks (bank_of_korea 부분: 메타데이터, 정제 텍스트, 문장 레이블 데이터)
- 라이선스: 레포 내 표기가 CC BY 4.0과 CC BY-NC-SA 4.0으로 섞여 있다. **파일별 적용 라이선스를 확인해야 한다**(확인 전에는 재배포·상업적 이용 금지로 간주).
- `data/raw/wcb/`의 `bank_of_korea_metadata.json`은 회의일을 바로잡은 새 버전이다. 회의일 오류가 있는 구버전(`old_bank_of_korea_metadata.json`)은 가져오지 않았다.

## WCB 모델
- Hugging Face: `gtfintechlab/model_WCB_stance_label`
- 접근 승인 대기 중. 승인 전까지 `models/`는 비어 있다.

## BOK 영문 의사록
- 한국은행 영문 홈페이지(https://www.bok.or.kr/eng)의 통화정책 의사록 페이지. 회의별 PDF 링크는 `meeting_master.csv`의 `minutes_link` 열에 있다.
- 수동 수집 16건(2024-10 ~ 2026-08, `date_source = BOK PDF (manual)`): 확인 날짜 2026-10-16.

## WCB HF 미리보기 (69행)
- `data/raw/wcb/wcb_hf_preview_69rows.csv`: Hugging Face 데이터셋 `bank_of_korea` 미리보기 69행. 2026-10 수동 복사(열: `row_no, sentences, stance_label, time_label, certain_label, year, hf_index`).
- 69행은 모두 `final_data.csv`에 포함된다(정규화 텍스트 일치로 확인). 문장별 판정 기록은 없다. 예비 감사 결과를 대체하는 것은 아니며, P3 전체 감사로 대체한다.

## 한국어 의사록 공개일
- `data/metadata/ko_release_dates.csv`: 2023-04-11 이후 28회의 BOK 한국어 홈페이지 공개일. 사용자 수동 수집(2026-10-17). `meeting_master.csv`의 영문 공개일이 있는 12건과 일치함을 확인했다.
