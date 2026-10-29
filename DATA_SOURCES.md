# 데이터 출처

## WCB 레포지토리
- https://github.com/gtfintechlab/WorldCentralBanks (bank_of_korea 부분: 메타데이터, 정제 텍스트, 문장 레이블 데이터)
- 라이선스: 레포 내 표기가 CC BY 4.0과 CC BY-NC-SA 4.0으로 섞여 있다. **파일별 적용 라이선스를 확인해야 한다**(확인 전에는 재배포·상업적 이용 금지로 간주).
- `data/raw/wcb/`의 `bank_of_korea_metadata.json`은 회의일을 바로잡은 새 버전이다. 회의일 오류가 있는 구버전(`old_bank_of_korea_metadata.json`)은 가져오지 않았다.

## WCB 모델
- 공식 모델 Hugging Face `gtfintechlab/model_WCB_stance_label`은 접근 승인 대기 중이며 본 분석에는 쓰지 않는다. 대신 아래 공개 데이터로 논문 설정대로 재현 학습한 모델(`models/wcb_stance_replica/`)을 쓴다. 승인되면 코퍼스 예측 일치도 보고에만 사용한다.

## WCB 공개 학습 데이터 (HF)
- Hugging Face 데이터셋 `gtfintechlab/all_annotated_sentences_25000`, 서브셋 `5768`, `78516`, `944601`(분할 시드). 각 서브셋 train 17,500 / val 3,750 / test 3,750. 인증 없이 받았다(2026-10-30). 저장 위치: `data/raw/wcb_hf/{seed}/{train,val,test}.parquet`(읽기 전용). 취득 스크립트 `scripts/10_download_wcb_hf.py`, 점검 `scripts/11_check_wcb_hf.py`.
- 라이선스: **CC BY-NC-SA 4.0**(비상업, 동일 조건 변경 허락). 이 데이터로 학습한 재현 가중치를 공개하려면 같은 라이선스를 적용한다.
- 점검 결과: 분할 시드 944601의 `bank_of_korea` 행은 train 661 / val 169 / test 170(합 1,000)이며 `final_data.csv`와 문장·라벨이 모두 일치한다. 서브셋 안에 분할 간 중복 문장이 4~10건 있다(원본 그대로 둠).

## BOK 영문 의사록
- 한국은행 영문 홈페이지(https://www.bok.or.kr/eng)의 통화정책 의사록 페이지. 회의별 PDF 링크는 `meeting_master.csv`의 `minutes_link` 열에 있다.
- 수동 수집 16건(2024-10 ~ 2026-08, `date_source = BOK PDF (manual)`): 확인 날짜 2026-10-16.

## WCB HF 미리보기 (69행)
- `data/raw/wcb/wcb_hf_preview_69rows.csv`: Hugging Face 데이터셋 `bank_of_korea` 미리보기 69행. 2026-10 수동 복사(열: `row_no, sentences, stance_label, time_label, certain_label, year, hf_index`).
- 69행은 모두 `final_data.csv`에 포함된다(정규화 텍스트 일치로 확인). 문장별 판정 기록은 없다. 예비 감사 결과를 대체하는 것은 아니며, P3 전체 감사로 대체한다.

## 한국어 의사록 공개일
- `data/metadata/ko_release_dates.csv`: 2023-04-11 이후 28회의 BOK 한국어 홈페이지 공개일. 사용자 수동 수집(2026-10-17). `meeting_master.csv`의 영문 공개일이 있는 12건과 일치함을 확인했다.
