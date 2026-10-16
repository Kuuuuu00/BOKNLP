# BOKNLP 작업 계획서 (plan.md)

- 작성일: 2026-10-17, 갱신: 같은 날 (연구계획서 갱신본, 주석 가이드 v1.1, 사용자 결정 D1~D12 반영)
- 기준 문서: `docs/BOK_의사록_스탠스_연구계획서.md` (이하 "계획서")와 `docs/annotation_guide.md` v1.1 (이하 "가이드"). 이 문서는 연구 설계를 바꾸지 않고, 실행 순서·산출물·완료 기준만 정한다.
- 설계상 의문점은 본문에 반영하지 않고 맨 끝 "검토 요청"에 모았다. 1차 검토 요청 중 계획서에 반영된 항목은 8절에 "해결"로 표시했다.
- 수치는 2026-10-17에 저장소 파일에서 직접 확인한 값이다. 확인하지 못한 것은 "미확인", 계산한 추정치는 "추정"이라고 적었다.

## 목차

0. 현재 상태 요약
1. 작업 원칙
2. 단계별 작업 (P1~P10)
3. 의존성과 차단 요소
4. 일정 (2026-10-19 ~)
5. 사용자 결정 목록
6. 산출물 대응표
7. 위험과 대응
8. 검토 요청

---

## 0. 현재 상태 요약

| 구분 | 항목 | 근거 |
|---|---|---|
| **완료** | 회의 163건 = WCB 147 + BOK 수동 수집 16. 정례 162회, 긴급회의 2020-03-16은 `regular=0`, `in_main_sample=0` | `meeting_master.csv` (`regular` 1:162/0:1, `in_wcb` 1:147/0:16, `date_source` WCB metadata 147 / BOK PDF (manual) 16) |
| **완료** | PDF 163개 manifest 대조 통과(크기·SHA-256·마스터 1:1·`final_data.csv` 1,000행·LFS 아님) | `scripts/07_verify_manifest.py` 종료코드 0 (2026-10-17 실행) |
| **완료** | `data/raw/` 파일 312개 전부 읽기 전용 속성 | 파일 속성 점검 (쓰기 가능 파일 0) |
| **완료** | uv 프로젝트 구성 (Python 3.12, torch 2.14.1+cu126, CUDA 인식 True, transformers 5.20.1) | `pyproject.toml`, `uv.lock` |
| **완료** | PDF 구조 진단(앵커·제목·머리글·각주 후보), 시기별 샘플 5개 | `data/interim/structure_report.csv`, `data/interim/samples/` |
| **완료** | WCB 라벨 `final_data.csv`: 1,000행, 열 `sentences, stance_label, time_label, certain_label, year`(2010~2024). stance 분포 dovish 343 / hawkish 340 / neutral 281 / irrelevant 36 | `final_data.csv` 직접 집계 |
| **진행 가능** | P1 위원 토의 범위 추출, P2 문장 분할·표결 문장 표시 | PDF와 구조 진단 완료 |
| **진행 가능** | P3 WCB 라벨 방향 감사 (`final_data.csv` 사용) | 모델 불필요 |
| **진행 가능** | P7 시장 데이터 수집(ECOS·FRED) | ECOS 키는 `.env`의 `ECOS_API_KEY`(완료, 값은 읽지 않음). FRED는 `fredgraph.csv`로 키 없이 수집 |
| **진행 가능** | P4 중 모델 없이 준비 가능한 부분(추론 스크립트 골격, 입력 형식 점검) | `torch`·`transformers` 설치됨, GPU 인식 |
| **차단** | P4 분류기 재현·추론 | WCB 모델(`gtfintechlab/model_WCB_stance_label`, HF gated) 접근 승인 대기. `models/` 비어 있음 |
| **차단** | P4 재현 점검의 테스트 150문장 | HF 시드 분할 데이터 접근 승인 대기. 저장소의 `final_data.csv`에는 분할 열이 없음 |
| **차단** | P5-d 한국 맥락 감사 50문장, P6 이후 전부 | P4 산출물(문장별 스탠스)에 의존 |
| **미착수** | 위원 토의 추출, 문장 분할, 표결 문장 제거, 토픽 라벨링, 분류기 추론, 지수 산출, 시장 데이터(ECOS·FRED) 수집 | `data/processed/` 비어 있음, `data/interim/`에 구조 진단 결과만 있음 |
| **완료** | 사용자 제공 파일 반영: 계획서 갱신본(`docs/`), 주석 가이드 v1.1(`docs/annotation_guide.md`), 한국어 공개일 28회(`data/metadata/ko_release_dates.csv`), WCB HF 미리보기 69행(`data/raw/wcb/wcb_hf_preview_69rows.csv`, 읽기 전용) | `ko_release_dates.csv`의 28개 회의가 `meeting_master.csv`의 2023-04-11 이후 회의와 1:1, 영문 공개일 12건 모두 한국어 공개일과 일치(직접 확인). 미리보기 69행은 모두 `final_data.csv`에 포함(정규화 텍스트 일치). 문장별 판정 기록은 없음 |
| **미확인** | 예비 감사 69문장의 문장별 판정 기록 | 제공된 것은 69행 원자료뿐이며 판정 기록은 없다. P3 전체 감사로 대체하고, 계획서 4.4절 수치(일치 18 / 애매 2 / 불일치 1)만 인용한다 |
| **대기 (사용자)** | D12 OpenAI 크레딧 충전(현재 5달러) | P5-a 전체 라벨링 전까지 필요 (5절) |

**문서 구조 3시기와 앵커 커버리지** (`structure_report.csv`, 문서 수 24 / 111 / 28. 긴급회의 2020-03-16은 가운데 시기에 포함)

| 시기 | START 앵커 중 하나라도 | END 앵커 중 하나라도 | 주요 앵커별 발견율 | 비고 |
|---|---|---|---|---|
| 2010~2011 | 100% | 100% | `Discussion Related to Monetary Policy Decision` 54%, `...on changes in the Bank of Korea Base Rate were as follows` 50%, `< Ref >` 100%, `After the discussions detailed above` 79%, `Remarks by Government Representative` 96% | 로마숫자가 제목과 다른 줄에 분리되어 제목 줄 정규식에는 안 잡힘 |
| 2012~2023.2 | 100% | 100% | `...concerning a change...` 94%, `Results of Deliberation` 89%, `< Ref >` 69% | 2012-05~12 (8회)는 Ⅳ(심의 결과) 없음. 2013-04-11, 2016-03-10, 2019-02-28은 `Ⅲ.`과 `Discussions`가 줄로 갈라져 로마숫자 목록에 Ⅲ이 빠졌을 뿐 제목은 존재 |
| 2023.4~ (28건) | 100% (일반 패턴 `Discussions? (on\|concerning\|related to)`만) | **0%** | END 앵커 없음 | Ⅰ Outline / Ⅱ Discussions Concerning the Monetary Policy Decision 2단. 끝 위치 규칙이 별도로 필요. 2023-07-13은 두 번째 제목이 `Ⅰ.`로 오기 |

(2023-01-13, 2023-02-23은 Ⅰ~Ⅳ 구성이고, 2단 구성은 2023-04-11부터다.)

---

## 1. 작업 원칙

### 1.1 재현성

- 스크립트는 `scripts/`에 **09번부터** 번호순으로 추가한다. 이미 쓰인 번호는 00, 01, 03, 04, 05, 07, 08이다(02, 06은 결번).
- 모든 스크립트는 입력·출력 경로를 인자로 받는다(`argparse`, 기본값은 이 문서의 경로). 저장소 루트에서 `uv run python scripts/<파일>`로 실행한다.
- 중간 산출물은 `data/interim/`, 분석용 최종 데이터와 표는 `data/processed/`, 새로 받는 외부 원자료는 `data/raw/<출처>/`에 둔다. 기존 `data/raw/` 파일은 읽기 전용이므로 수정하지 않는다.
- 파일 갱신이 생기는 단계가 끝나면 `uv run python scripts/07_verify_manifest.py`를 다시 돌려 원자료가 변하지 않았음을 확인한다.
- `data/`는 gitignore 대상이므로 산출물은 커밋되지 않는다. 대신 **스크립트·`plan.md`·표 정의만 커밋**하고, 산출물의 행 수·SHA-256은 단계별 완료 기록(`data/interim/RUNLOG.md`, 커밋 안 됨)에 남긴다. 이 기록 방식은 5절의 결정 대상이 아니라 기본 방침이며 필요하면 바꾼다.
- API 키는 저장소 루트 `.env`(gitignore 대상)에 둔다: `ECOS_API_KEY`, `OPENAI_API_KEY`(값은 사용자가 입력). 키가 필요한 스크립트는 `uv run --env-file .env python scripts/<파일>`로 실행한다. 키 값은 로그·출력·산출물에 남기지 않는다.
- 난수가 들어가는 단계(층화 추출, 부트스트랩)는 `--seed`를 인자로 받고 값을 산출물 옆 `*.meta.json`에 기록한다.

### 1.1b 판정 기준과 사람·LLM 역할 (가이드 v1.1)

| 가이드 | 판정 내용 | 쓰는 단계 | 담당 |
|---|---|---|---|
| **A 토픽** | 문장당 토픽 하나 (Macro / FinStab / External / Other) | P5-0, P5-a, P5-b, P5-c | **LLM(전체 문장) + 사람(개발 40, 검증 120)** |
| **B 한국 맥락 스탠스 감사** | WCB 라벨·예측의 방향이 5.3절 기준과 맞는지 | P3, P5-d | **사람만** |
| **C 섹션·표결 검수** | 위원 토의 경계, `is_vote`, `is_boilerplate` | P1, P2 (같은 20문서) | **사람만** |

- LLM은 토픽(A)만 맡는다. B와 C는 LLM에 맡기지 않는다.
- 공통 원칙(가이드): 문장 단위·눈가림(사람은 LLM 토픽과 WCB 스탠스를 보지 않고 판정한 뒤 병합)·검증 표본 판정 시작 후 가이드 수정 금지(고치면 버전을 올리고 처음부터 다시)·애매 표시.
- **가이드 A4 예시 11문장은 개발·검증 표본에서 제외한다.** `final_data.csv` 행 번호(0부터) 32, 56, 435, 295, 165, 99, 629, 307, 23, 660, 31이다. 정규화 텍스트(소문자, 공백 정리, 곡선 따옴표 `’`를 `'`로 통일)가 일치하는 코퍼스 문장을 제외 대상으로 삼는다(`final_data.csv`와는 11건 모두 일치함을 확인).

### 1.2 사전 고정 규칙의 순서 제약 (계획서 2.2절)

| 규칙 | 순서 제약 | 구현 방법 |
|---|---|---|
| (a) 5.3절 감사 통과 기준 (불일치 30% 미만) | **회귀(P8) 전에** 판정 완료. 판정 결과가 모형 2의 FinStab·External 계수 해석 방식을 정한다 | P5-d에서 판정을 `data/processed/audit_korea_context_result.json`에 기록하고, P8 스크립트가 이 파일이 없으면 종료한다 |
| (b) ΔS_{t-1} 포함 여부 | 지수 산출 직후, **금리 데이터를 쓰지 않고** ρ1 검정(6.4절)으로 결정. 결과를 `rho1_test.json`에 기록한 뒤에만 시장 데이터를 병합 | P6에서 결정하고 git tag `index-frozen` |
| (c) 주 만기와 검정 | 주 만기는 3년물, 10년물은 보조. H2·H3는 HC3 강건 Wald 검정(자유도 3, 2). 조정 R²는 보고만 한다 | P8 스크립트 상수로 고정하고 변경하지 않는다 |

### 1.3 금리 데이터 격리 규칙

- 시장 데이터(ECOS, FRED)는 **먼저 수집해도 되고**, 지수와 무관한 정리(`Δi_t`, `Spread`, `D^inv`, `D^freq`, 역전 구간 경계와 회의 수 세기)까지는 해도 된다.
- 그러나 **git tag `index-frozen`을 찍기 전에는** 시장 데이터와 지수를 병합하거나 회귀·상관·그림에 함께 쓰지 않는다. Table 2의 ΔS_t–Δi_t 상관도 tag 이후에 계산한다.
- 기계적 보장: `scripts/22_*` 이후(병합·회귀·강건성·그림) 스크립트는 시작 시 `git tag --list index-frozen`이 비어 있으면 종료코드 1로 멈추고, tag가 가리키는 커밋 이후 `stance_index.csv`가 바뀌었는지(SHA-256을 `rho1_test.json`에 기록해 대조) 확인한다.
- tag 이후 지수를 고치려면 사용자 결정이 필요하며(5절), 고치면 시장 데이터를 본 뒤의 수정이라는 사실을 `RUNLOG.md`에 기록한다.

### 1.4 검증 원칙

- 모든 단계에 **완료 기준**(수치 또는 파일 존재 조건)을 둔다. 기준을 못 맞추면 다음 단계로 가지 않고 7절의 대응을 따른다.
- 사람이 보는 검수(20문서, 라벨 방향, 50문장, 직접 토픽 라벨)는 표본 추출 목록과 판정 결과를 CSV로 남긴다.

---

## 2. 단계별 작업

표기: 선행 = 먼저 끝나야 하는 단계, 계획서 절 = 근거.

### P1. 위원 토의 범위 추출

- **목적:** 각 PDF에서 위원 토의(경제 상황 토의 + 통화정책 결정 토의) 본문만 뽑는다. 개요, 정부 측 발언, 심의 결과, 결정문(< Ref >), 표결 의견 문장은 제외(계획서 4.1절 표).
- **선행:** 없음. **계획서 절:** 4.1, 5.1, 5.5(20문서 검수). 검수 판정 기준은 **가이드 C**.
- **입력:** `data/raw/pdf/*.pdf`, `data/interim/structure_report.csv`
- **스크립트:** `scripts/09_extract_discussion.py` (`--pdf`, `--out`, `--diagnose`)
- **출력:**
  - `data/interim/discussion_blocks.csv` — `meeting_date, block_id, section(econ|policy|discussion), page_start, page_end, text_raw, extract_method(title|anchor|manual), start_rule, end_rule, n_chars, flag`
  - `data/interim/section_manual_queue.csv` — `meeting_date, reason, detail` (자동 추출 실패·의심 문서)
  - `data/interim/font_size_report.csv` — `meeting_date, body_size, footnote_size_candidates` (각주 글자 크기 진단)
- **작업 목록**
  - [ ] 글자 크기 진단(`--diagnose`): 본문 크기와 각주 크기를 문서별로 요약. 시기별로 달라지는지 확인(2010~2011, 2012~2023.2, 2023.4~)
  - [ ] **시기별 시작·끝 규칙 설계** (`structure_report.csv` 근거). 1순위는 섹션 제목 텍스트, 2순위는 문구 앵커, 둘 다 실패하면 `section_manual_queue.csv`로 보낸다.

    | 시기 | 시작 (1순위 제목 / 2순위 앵커) | 끝 |
    |---|---|---|
    | 2010~2011 | 제목 `Discussion of Economic Situation`, `Discussion Related to Monetary Policy Decision` (번호가 별도 줄로 분리된 형태를 합쳐 인식) / 앵커 `Discussions? (on\|concerning\|related to)` | 정부 측 발언 제목(`Remarks by (the )?Government Representative`)은 구간에서 **제외**하고, 결정문 `< Ref >` 또는 `After the discussions detailed above` 직전까지 |
    | 2012~2023.2 | 제목 `Ⅱ. Summary of Discussion(s) on the Current Economic Situation`, `Ⅲ. Discussions ... Monetary Policy Decision` (제목이 줄로 갈라진 3건 처리 포함) / 앵커 `...concerning a change in the Bank of Korea Base Rate were as follows` | `Results of (the )?Deliberation`(Ⅳ) 직전. Ⅳ가 없는 2012-05~12(8회)는 `< Ref >` 직전, 그것도 없으면 문서 끝 |
    | 2023.4~ | 제목 `Discussions Concerning the Monetary Policy Decision` (단일 섹션, 2023-07-13은 번호가 `Ⅰ.`로 오기이므로 번호가 아니라 제목 텍스트로 인식) | END 앵커가 없으므로 문서 끝. 문서 끝의 쪽번호·꼬리말만 제거하고, 문서 끝에 다른 섹션이 붙지 않는지 샘플로 확인 |
  - [ ] 로마숫자가 아니라 **제목 문구**로 구간을 정한다(번호 오기, 줄 분리에 영향받지 않게)
  - [ ] **글자 크기 기반 각주 제거**: 본문 크기보다 작은 span 제거, `1)` 형태의 각주 번호가 제목·본문 끝에 붙은 경우(`...Economic Situation2)`) 제거
  - [ ] 쪽번호(`- n -`), 머리글·꼬리말 제거 (`structure_report.csv`의 `header_footer` 후보 사용, 2022년 후보가 비어 있는 원인 확인)
  - [ ] 하이픈·줄바꿈 복원(단어 중간 하이픈 연결, 문장 중간 줄바꿈 연결, 글머리표 `-`·`•` 처리)
  - [ ] `section` 열 기록: 2012~2023.2는 Ⅱ=econ, Ⅲ=policy. 2010~2011도 같은 방식. 2023.4~는 `discussion`(단일 섹션). 계획서 5.1절대로 기록용이며 분석에는 쓰지 않는다
  - [ ] **개별 처리**: 2023-07-13(두 번째 제목 번호 `Ⅰ.`), 2013-04-11·2016-03-10·2019-02-28(Ⅲ 제목 줄바꿈), 2012-05-10~2012-12-13(Ⅳ 없음), 2020-03-16(긴급회의, 구성 별도 확인)
  - [ ] 20문서 층화 검수(시기별 비례, 시드 고정, **P2 검수와 같은 20문서**, 가이드 C1·C4): 구간 시작·끝 쪽이 맞는지 눈으로 확인하고 `data/interim/audit_sections_20.csv`(`meeting_date, era, start_ok, end_ok, leftover_footnote, memo`)에 기록
- **완료 기준:** (i) 163개 문서가 `discussion_blocks.csv`에 있거나 `section_manual_queue.csv`에 사유와 함께 있다. (ii) 수작업 대기열은 모두 수동 해결되어 비어 있다. (iii) 20문서 검수에서 구간 경계 오류 0건(1건 이상이면 규칙 수정 후 다른 20문서로 재검수). (iv) 각주 번호가 문장 끝에 남아 있는 비율을 보고(목표값은 5.5절에 없으므로 보고만 함).

### P2. 문장 분할과 표결 문장 제거(표시)

- **목적:** 구간 텍스트를 문장으로 나누고, 표결 의견 문장과 도입 boilerplate를 **삭제하지 않고 표시**한다(계획서 5.1절).
- **선행:** P1. **계획서 절:** 5.1, 5.5. 판정 기준은 **가이드 C2(표결 문장)·C3(도입 문장)**, 기록은 C4(`ok|missed|over`).
- **입력:** `data/interim/discussion_blocks.csv`
- **스크립트:** `scripts/10_split_sentences.py` (`--in`, `--out`, `--audit-seed`)
- **출력:**
  - `data/interim/sentences.csv` — `meeting_date, sent_id, block_id, section, sent_raw, sent_norm, is_vote, vote_rule, is_boilerplate, boilerplate_rule, n_chars`
  - `data/interim/sentence_count_by_meeting.csv` — `meeting_date, era, n_all, n_vote, n_boilerplate, n_usable`
  - `data/interim/audit_votes_20.csv` — 검수 표본 20문서(P1과 같은 문서 사용 가능): `meeting_date, sent_id, sent_raw, is_vote, reviewer_judgment(ok|missed|over), memo`
- **작업 목록**
  - [ ] **문장 분할기: `pysbd`** (D10 확정). P2 시작 시 `uv add pysbd`로 추가하고 `pyproject.toml`·`uv.lock`을 커밋. 약어(`U.S.`, `e.g.`), 소수점, `%`, 괄호 처리 결과를 샘플로 점검
  - [ ] **두 열 유지:** `sent_raw`(원문, LLM 토픽·정규식·검수용), `sent_norm`(소문자화·공백·특수문자 정리, **스탠스 분류기 입력 전용**)
  - [ ] `is_vote` 표시 규칙(계획서 5.1절 패턴): `(most|a majority of|some) members shared the opinion that ... (raise|lower|cut|keep) ... base rate`, `it would be (appropriate|desirable|best) to (raise|lower|cut|keep|leave|hold) the base rate ... (at this meeting|this month)`, `argued that the base rate should be kept ...`. 어떤 규칙에 걸렸는지 `vote_rule`에 기록
  - [ ] `is_boilerplate` 표시: "After hearing staff briefings…" 류 정해진 도입 문장. 규칙 목록은 `sent_raw` 빈도 상위 문장에서 도출
  - [ ] 회의별 문장 수 분포 보고: 시기별 중앙값·최소·최대. 경고 기준은 D9 확정: **분모 `N_tot − N_irr` < 10인 회의는 경고만 하고 제외하지 않는다**(분모 확정은 P6이므로 P2에서는 `n_usable` 기준 분포와 잠정 경고만, P6에서 최종 경고 목록 보고)
  - [ ] 20문서 층화 검수(5.5절, 가이드 C): 놓친 표결 문장 비율, 과잉 제거 비율을 보고. 향후 경로·조건부 서술은 표결 문장이 아니다(가이드 C2) — 과잉 제거 점검의 핵심
- **완료 기준:** (i) 163문서 모두 `n_usable ≥ 1`. (ii) 20문서 검수 결과의 놓친 비율·과잉 제거 비율을 수치로 보고(통과 기준은 계획서에 없으므로 보고 후 사용자가 판단 — 7절 "표결 정규식 과잉 제거" 참조). (iii) `is_vote`·`is_boilerplate`는 열로만 존재하고 어떤 행도 삭제되지 않았다(`sent_id` 연속성 확인).

### P3. WCB 라벨 방향 감사 (전체)

- **목적:** `final_data.csv`에서 원화·외환·주택·부채·금리차 관련 문장 전체의 방향이 5.3절 기준과 맞는지 감사해 "가이드 표 65 오기" 판단을 확정한다(계획서 4.4절, 5.5절).
- **선행:** 없음(모델 불필요). **계획서 절:** 4.4, 5.3, 5.5. 판정 기준은 **가이드 B**(WCB 라벨을 보지 않고 `expected_direction`을 먼저 기록).
- **입력:** `data/raw/wcb/final_data.csv`
- **스크립트:** `scripts/11_audit_wcb_labels.py`
- **출력:**
  - `data/interim/wcb_label_audit_candidates.csv` — `row_id, year, sentences, stance_label, keyword_hits, expected_topic`
  - `data/interim/wcb_label_audit.csv` — 위 열 + `row_type(orig|symmetric)`(5.3절 원래 행 / 대칭 행), `expected_direction(hawkish|dovish)`, `judgment(일치|애매|불일치|대상아님)`, `memo`
  - `data/processed/table1_label_audit.csv` — `row_type(orig|symmetric), category, n, n_agree, n_ambiguous, n_disagree, disagree_rate`(불일치율 = 불일치 / (일치 + 불일치), 애매는 분모에서 빼고 개수를 따로 보고. **원래 행과 대칭 행은 나누어 집계**)
- **작업 목록**
  - [ ] 키워드(원화, won, exchange rate, 환율, housing, household debt, 연체 delinquen*, Fed, interest rate differential 등)로 후보 추출. 키워드 목록과 후보 수를 기록(후보 수는 아직 모름)
  - [ ] 5.3절 표(대칭 행 포함, D11) 기준으로 `expected_direction`과 `judgment` 기록 (직접 판정, 가이드 B2)
  - [ ] 예비 감사 69문장: 원자료 `data/raw/wcb/wcb_hf_preview_69rows.csv`(69행 모두 `final_data.csv`에 포함, 문장별 판정 기록 없음, D7). 전체 감사에 흡수되므로 별도 비교 없이 계획서 4.4절의 예비 수치(일치 18 / 애매 2 / 불일치 1)와 전체 결과를 나란히 보고
  - [ ] "accommodative" 단어에 끌린 라벨 사례 별도 표시
  - [ ] 하방 금융불안 문장(주택가격 급락·연체 증가)의 라벨 방향 분포 별도 집계
- **완료 기준:** (i) 후보 전체에 `judgment`가 채워짐. (ii) 매파/비둘기 열이 뒤바뀌었는지 여부(표 65 오기 판단)를 확정하는 한 줄 결론을 `data/processed/table1_label_audit.csv` 옆 메모에 기록. (iii) 예비 감사(일치 18 / 애매 2 / 불일치 1)와 전체 결과를 나란히 보고.

### P4. 분류기 (차단: 모델·데이터 접근 승인)

- **목적:** WCB 통합 4진 모델을 미세조정 없이 그대로 써서 (a) 논문 F1(0.755)을 재현하고, (b) 전체 문장에 대해 추론한다(계획서 5.2절).
- **선행:** 승인(모델·시드 분할 데이터). 추론은 P2. **계획서 절:** 5.2, 5.5, 부록 A.

**P4-0. 승인 전에 준비할 수 있는 것 (지금 진행 가능)**

- [ ] `scripts/12_repro_wcb_model.py`, `scripts/13_infer_stance.py` 골격 작성: 모델 경로·라벨 매핑·배치 크기·최대 길이·`do_lower_case`를 인자로 받고, 승인 전에는 모델이 없다는 메시지로 종료
- [ ] 입력 형식 점검: `final_data.csv`의 `sentences` 열을 `sent_norm`과 같은 규칙으로 정규화했을 때 어떤 차이가 나는지 비교하는 함수(승인 전에도 가능)
- [ ] GPU 메모리·배치 크기 사전 점검은 모델 확보 후(미확인: RTX 4070 Ti의 VRAM 용량은 직접 확인하지 않음)
- [ ] 승인 상태 확인 절차: `hf auth whoami` 후 모델 페이지 접근 확인(사용자 로그인 필요, 5절 D3)

**P4-a. 설정 확인 (승인 직후)**

- 스크립트: `scripts/12_repro_wcb_model.py --check-config`
- [ ] `config.json`으로 기반 모델 크기(모델 카드는 roberta-base, 논문은 large) 확인
- [ ] 라벨 id → {hawkish, dovish, neutral, irrelevant} 매핑 확인
- [ ] 학습에 쓰인 분할 시드 확인(모델 카드 / GitHub 학습 설정, 부록 A)
- 출력: `data/interim/wcb_model_config.json` — `base_model, num_labels, id2label, train_seed, model_revision`

**P4-b. 재현 점검**

- 스크립트: `scripts/12_repro_wcb_model.py --split-seed <시드>`
- [ ] **WCB 통합 모델이 학습에 쓴 분할의 테스트 150문장**으로만 가중·매크로 F1 계산(다른 시드의 테스트셋은 학습 문장이 섞일 수 있으므로 쓰지 않음, 계획서 4.4절)
- [ ] 부트스트랩 신뢰구간(`--seed` 고정), 논문 0.755(±0.019)와 비교
- 출력: `data/processed/table1_repro_f1.csv` — `metric(weighted_f1|macro_f1), value, ci_low, ci_high, paper_value`
- **완료 기준:** 가중 F1과 논문 값의 차이를 보고한다. 통과 숫자 기준은 계획서에 없다(목적은 "논문과 같은 방식으로 쓰고 있는지 확인"). 차이가 크면 7절의 대응(원인 점검 후 결정 요청)

**P4-c. 전체 문장 추론 (GPU)**

- 스크립트: `scripts/13_infer_stance.py --in data/interim/sentences.csv --out data/interim/sentence_stance.csv`
- 입력은 `sent_norm`만 쓴다. `is_vote`·`is_boilerplate` 행도 **추론은 하되** 지수 산출(P6)에서 제외한다(나중에 규칙을 바꿔도 재추론하지 않도록).
- 출력: `data/interim/sentence_stance.csv` — `sent_id, pred_label, p_hawkish, p_dovish, p_neutral, p_irrelevant, model_revision`
- **완료 기준:** `sentences.csv`의 모든 `sent_id`에 예측이 있다(행 수 일치, 결측 0). 같은 입력을 다시 돌려 예측이 동일(결정적 실행).

### P5. 토픽 라벨링과 한국 맥락 감사

- **목적:** 문장마다 토픽 하나(Macro / FinStab / External / Other)를 LLM으로 붙이고, 직접 라벨과의 κ를 검증하고, WCB 판정을 한국 맥락에서 감사한다(계획서 5.3~5.5절).
- **선행:** P2(P5-0, P5-a, P5-b), P4-c(P5-d). **계획서 절:** 5.3, 5.4, 5.5.
- **판정 기준:** 토픽은 **가이드 A**, 감사는 **가이드 B**. LLM은 토픽(A)만 맡고 B는 사람만 한다(1.1b절).
- **고정 순서:** P5-0 → P5-a(개발 표본으로 프롬프트 수정 → 설정 고정 → 전체 라벨링) → P5-b → P5-c. **프롬프트 수정은 P5-a의 개발 표본 단계에서만** 한다. 설정 고정 뒤, 그리고 검증 표본을 본 뒤에는 고치지 않는다(계획서 5.4절).

**P5-0. 개발 표본 40문장 (사람)** — P2 후, 지금 계획상 2주차

- 스크립트: `scripts/15_sample_topic_labels.py --kind dev --n 40 --seed <값>` (검증 표본 추출과 같은 스크립트 사용)
- [ ] 코퍼스 문장(`is_vote=0`, `is_boilerplate=0`)에서 **무작위** 40문장 추출(시드 고정). **가이드 A4 예시 11문장과 일치하는 문장은 제외**(1.1b절)
- [ ] 사용자가 가이드 A로 직접 라벨(눈가림: LLM 토픽 없음)
- 출력: `data/interim/topic_dev_sample.csv` — `sent_id, sent_raw, human_topic, ambiguous, memo`
- **완료 기준:** 40문장 모두 `human_topic` 기입.

**P5-a. LLM 토픽 라벨링**

- 스크립트: `scripts/14_label_topics_llm.py` (`--model gpt-6.1-sol`, `--reasoning`, `--prompt-version`, `--in`, `--out`, `--cache`, `--dry-run`)
- **LLM(D1 확정):** GPT-6.1 Sol(`gpt-6.1-sol`), OpenAI Responses API 구조화 출력(`json_schema`, `strict: true`, 스키마는 가이드 부록). 추론 강도는 하나로 고정(권장 `low`). `temperature`는 모델이 지원하면 0, 아니면 설정하지 않고 그 사실을 기록. 응답의 `model` 필드(스냅샷 이름), 토큰 사용량, 원문 응답을 저장. 예상 비용 12~20달러(**추정**, 크레딧 충전 필요 — D12)
- **스크립트 요구사항**
  - [ ] **20문장 배치**, 각 문장에 `id`. 입력은 `sent_raw` 그대로이며 날짜·회의 정보는 주지 않는다
  - [ ] **입출력 id 1:1 검사:** 누락·중복·거절(refusal) 배치는 **같은 설정으로 1회 재시도**, 그래도 실패하면 수작업 목록(`data/interim/topic_manual_queue.csv`)으로
  - [ ] **캐시:** 문장 ID × `prompt_version`. 같은 키는 재호출하지 않는다
  - [ ] **요청·응답 원문 JSON 저장:** `data/interim/llm_logs/<prompt_version>/batch_<n>.json` (요청, 응답 전문, 응답 `id`, `model`, 추론 토큰 포함 사용량, refusal 여부)
  - [ ] **토큰 사용량과 누적 비용 로그:** 배치마다 누적 출력. 단가는 실행 시 인자로 받는다(이 문서에 적지 않음). 상한을 넘으면 중단하는 `--max-cost` 인자
  - [ ] **`--dry-run`:** API를 호출하지 않고 배치 수와 입력 토큰 수만 계산해 출력(키 없이도 동작)
  - [ ] `.env`의 `OPENAI_API_KEY`는 `uv run --env-file .env`로 전달받고 출력·로그에 남기지 않는다
- **단계**
  1. [ ] **개발 표본(P5-0)에 LLM 실행** → 사람 라벨과 비교해 불일치 사례 검토
  2. [ ] **프롬프트 수정은 이 단계에서만.** 수정할 때마다 `prompt_version`을 올린다(`topic-v1.0` → `v1.1` …)
  3. [ ] **같은 설정으로 2회 실행**해 LLM 자체 일치율 보고(가이드 부록 "재현성 점검")
  4. [ ] **모델 스냅샷·추론 강도·`prompt_version` 고정**, 프롬프트 전문과 few-shot 예시 ID를 `prompts/topic_<버전>.md`에 **커밋**
  5. [ ] 고정된 설정으로 **전체 문장 라벨링** (`is_vote`·`is_boilerplate` 문장은 호출 대상에서 제외하되 `sent_id`는 보존)
- 출력: `data/interim/sentence_topic.csv` — `sent_id, topic, ambiguous, reason, llm_model_snapshot, reasoning_effort, prompt_version, response_id`
- **완료 기준:** (i) 모든 대상 문장에 토픽이 있거나 수작업 목록에 있다. (ii) 고정된 `prompt_version`이 `prompts/`에 커밋되어 있다. (iii) 개발 표본 사람–LLM 일치율, LLM 2회 실행 일치율, 총 토큰·비용이 `RUNLOG.md`에 기록되어 있다.

**P5-b. 검증 표본 120문장 (사람)** — 설정 고정과 전체 라벨링 뒤

- 스크립트: `scripts/15_sample_topic_labels.py --kind val --n 120 --seed <값>`
- [ ] **LLM 토픽별 30문장 × 4, 시기별 비례 배분**(D8 확정). 개발 표본 40문장과 **가이드 A4 예시 11문장은 제외**
- [ ] 사용자가 가이드 A로 직접 라벨(**LLM 라벨 비공개**: 사용자에게 주는 파일에 LLM 열을 넣지 않고, 판정 뒤 병합)
- 출력: `data/interim/topic_val_sample.csv` — `sent_id, sent_raw, human_topic, ambiguous, memo` (병합본은 `topic_val_merged.csv`에 `llm_topic` 추가)
- 시기 층: 2010~2011 / 2012~2023.2 / 2023.4~ (3층, 문장 수 비례). 최소 표본이 부족한 층은 보고

**P5-c. 토픽별 Cohen's κ**

- 스크립트: `scripts/16_topic_kappa.py`
- [ ] **토픽별 이진 κ**(해당 토픽 대 나머지, 계획서 5.4절) + **4개 토픽 전체 κ(참고)**
- [ ] 애매 판정 비율 보고
- [ ] **κ ≥ 0.6** 미달 토픽은 **Other에 합친다**(계획서 5.4절). Other는 합치지 않고 κ만 보고. 합치면 H2 Wald 자유도 = 남은 토픽 수 − 1 (계획서 2.1절). FinStab·External이 합쳐지면 한국 특화 해석이 약해진다는 점을 결과에 밝힌다
- 출력: `data/processed/table1_topic_kappa.csv` — `topic, n_human, kappa_binary, kappa_overall_ref, ambiguous_rate, merged_into`

**P5-d. 한국 맥락 WCB 판정 감사 50문장 (사람, 가이드 B)** — P4-c 필요

- 스크립트: `scripts/17_audit_korea_context.py`
- [ ] LLM이 FinStab·External로 분류한 문장에서 **FinStab 25 / External 25**, 시기별 문장 수에 비례해 배분(D8 확정, 시드 고정)
- [ ] 각 문장의 `expected_direction`을 **WCB 예측을 보지 않고** 먼저 기록(가이드 B2). 5.3절 표 기준(**대칭 행 포함**, D11). 대칭 행에 해당하는 문장은 `row_type=symmetric`으로 표시해 **원래 행과 나누어 집계**
- [ ] 불일치율 = 불일치 / (일치 + 불일치), 애매는 분모에서 빼고 개수를 따로 보고 → **30% 미만이면 통과**
- 출력: `data/interim/audit_korea_context_50.csv` — `sent_id, sent_raw, topic, row_type(orig|symmetric), pred_label, expected_direction, judgment(일치|애매|불일치|대상아님), memo`; `data/processed/audit_korea_context_result.json` — `n, n_agree, n_ambiguous, n_disagree, disagree_rate, by_row_type, pass`
- **완료 기준(5.3절):** 불일치율 < 30%면 `pass=true`로 WCB 지수를 그대로 사용. ≥ 30%면 `pass=false`: 모형 2의 FinStab·External 계수 해석을 유보하고 한계로 명시(P8에서 반영).

### P6. 지수 산출과 지수 확정

- **목적:** S_t, S^k_t(공통 분모), ΔS_t, ΔS^k_t를 만들고, 금리 데이터 없이 ρ1 검정으로 ΔS_{t-1} 포함 여부를 정한 뒤 지수를 확정한다(계획서 6절).
- **선행:** P2, P4-c, P5-a(토픽 라벨 전체, 설정 고정 뒤). 토픽 κ 결과(P5-c)와 감사 판정(P5-d)은 지수 값을 바꾸지 않지만 κ 미달로 토픽을 합치면 S^k 열이 바뀌므로 **P5-c 완료 후** 확정한다. **계획서 절:** 6.1~6.4.
- **입력:** `sentences.csv`, `sentence_stance.csv`, `sentence_topic.csv`
- **스크립트:** `scripts/18_build_index.py`, `scripts/18b_test_rho1.py`
- **출력:** `data/processed/stance_index.csv` — `meeting_date, regular, N_tot, N_irr, N_H, N_D, N_N, S, S_Mac, S_FS, S_Ext, S_Oth, dS, dS_Mac, dS_FS, dS_Ext, dS_Oth, dS_lag, n_vote_excluded, n_boilerplate_excluded, merged_topics`
  `data/processed/rho1_test.json` — `rho0, rho1, se_hc3, p_value, n, include_dS_lag(bool), stance_index_sha256, created_at`
- **작업 목록**
  - [ ] `N_tot` = 위원 토의 문장 중 `is_vote`·`is_boilerplate` 문장을 **뺀** 문장 수, `N_irr` = 그중 무관(irrelevant) 문장 수 (계획서 6.1절). **분모 `N_tot − N_irr` < 10인 회의는 경고만** 하고 제외하지 않으며, 경고 회의 목록을 보고 (D9, 계획서 6.1절)
  - [ ] `S = Σ_k S^k` 항등식 검사(모든 회의에서 오차 1e-12 이하)
  - [ ] 해당 토픽 문장이 없는 회의의 `S^k = 0` 처리
  - [ ] `S_{t-1}`은 **직전 정례 회의**의 지수(긴급회의 제외, 계획서 6.3절). 첫 회의(2010-01-08)는 ΔS 결측 → 본 회귀 관측치 **161회**
  - [ ] ρ1 검정: 금리 데이터를 읽지 않고 `ΔS_t = ρ0 + ρ1 ΔS_{t-1} + u_t`, HC3. 5% 유의하면 `include_dS_lag = true`
  - [ ] **지수 확정:** `stance_index.csv`를 커밋하지 않고(data/ 제외) SHA-256을 `rho1_test.json`에 기록한 뒤, 스크립트·프롬프트·설정 커밋에 **git tag `index-frozen`** 부착
- **완료 기준:** (i) 163회(정례 162 + 긴급 1)의 행이 있고 `regular` 열로 구분. (ii) 항등식 검사 통과. (iii) `rho1_test.json` 존재. (iv) tag `index-frozen` 존재.

### P7. 시장 데이터와 한국어 의사록 공개일

- **목적:** ECOS(국고채 3·10년, 기준금리), FRED(DGS2, DGS10, DFEDTARU)를 수집하고 `Spread`, `D^inv`, `D^freq`를 만든다. R9용 한국어 의사록 공개일은 **수집 완료**다(계획서 4.2절, 부록 A).
- **선행:** ECOS 키(`.env`, 완료). FRED는 `fredgraph.csv`로 키 없이 수집(D5). **언제든 수집 가능**하지만 **지수와의 병합은 P6 이후**(1.3절). **계획서 절:** 4.2, 7.1, 8(R9), 부록 A.
- **스크립트:** `scripts/19_fetch_market_data.py`(ECOS는 `uv run --env-file .env`), `scripts/20_build_market_panel.py`. 한국어 공개일은 수집 완료이므로 스크립트 `21`은 만들지 않는다(번호 21은 결번)
- **출력**
  - `data/raw/market/ecos_ktb3y.csv`, `ecos_ktb10y.csv`, `ecos_base_rate.csv`, `fred_dgs2.csv`, `fred_dgs10.csv`, `fred_dfedtaru.csv` — `date, value, source, fetched_at` (수집 후 읽기 전용 처리)
  - `data/interim/market_events.csv` — `meeting_date, Y3, Y3_prev, dY3, Y10, Y10_prev, dY10, dUST2_lag, dUST10_lag, bok_rate, bok_rate_prev, d_i, fed_upper_lag, spread_lag, D_inv, D_freq, prev_trading_day, us_prev_bday`
  - **(완료, 입력)** `data/metadata/ko_release_dates.csv` — `meeting_date, ko_release_date, lag_days_ko, lag_weekdays_ko, release_date_en, source`. 2023-04-11 이후 28회. **R9의 입력 파일이다.** `meeting_master.csv`와 1:1, 영문 공개일 12건은 한국어 공개일과 같은 날(직접 확인), 회의 후 18~21일
  - `data/interim/inversion_regimes.csv` — `regime_id, start_date, end_date, n_meetings` (역전 구간 경계와 회의 수, 계획서 추정 3차 약 16회·4차 약 34회를 **데이터로 다시 센다**)
- **작업 목록**
  - [ ] 회의 당일 `Y_t`와 직전 영업일 `Y_{t-1}` 정렬(한국 휴장일은 ECOS 일자 기준)
  - [ ] **미국 직전 영업일 정렬 규칙:** 한국 시간 회의일 t에 대해 `ΔUST_{t-1}`은 t 이전의 가장 최근 미국 영업일 하루 변화(bp). 미국 휴장일에 걸리면 그 이전 영업일 사용. 규칙을 함수 하나로 구현하고 단위 점검(예: 회의일이 월요일일 때)
  - [ ] `Spread_{t-1}` = 회의 전날 (BOK 기준금리 − 연방기금금리 목표 상단). 결측일은 직전 값 이월
  - [ ] `D_freq`: 2017년 이후 1 (`meeting_master.csv`의 `freq_regime`과 일치하는지 대조: 0이 84, 1이 79)
  - [x] 한국어 의사록 공개일 수집 완료(D6). 공개 시각은 수집되지 않았다(계획서 부록 A에서 R9 사건일 t 또는 t+1 판단용이므로 R9 단계에서 다시 결정)
  - [ ] `scripts/20`에는 지수 파일을 읽는 코드가 없어야 한다(코드 리뷰 항목)
- **완료 기준:** (i) 모든 정례 회의일에 `dY3`, `dY10`, `d_i`가 결측 없이 있다(결측이 있으면 사유 목록). (ii) `D_inv`가 `inversion_regimes.csv`의 구간과 일치. (iii) `ko_release_dates.csv`의 28회 공개일이 `market_events.csv`와 날짜 정렬이 되는지(공개일이 한국 영업일인지) 확인.

### P8. 본 회귀

- **목적:** 모형 1~3을 3년물·10년물에 대해 추정하고 H2·H3 Wald 검정을 한다(계획서 7.1~7.2절).
- **선행:** P6(tag `index-frozen`), P5-d(`audit_korea_context_result.json`), P7. **계획서 절:** 2.1, 2.2, 6.4, 7.
- **스크립트:** `scripts/22_merge_and_describe.py`, `scripts/23_regressions.py`
- **출력:**
  - `data/processed/analysis_panel.csv` — `stance_index.csv`의 열 + `market_events.csv`의 열 (정례 162회, 이 중 ΔS 결측 1건 제외 시 161, 계획서 6.3절)
  - `data/processed/table2_descriptives.csv` — 주요 변수 기술통계, ΔS_t–Δi_t 상관, ρ1과 검정 결과, 역전·비역전 회의 수, 금리 결정 분포
  - `data/processed/table3_main_regressions.csv` — `model(1|2|3), maturity(3Y|10Y), term, coef, se_hc3, t, p, n, adj_r2, wald_stat, wald_df, wald_p`
- **작업 목록**
  - [ ] 통제변수: 3년물 식 `ΔUST2Y_{t-1}`, 10년물 식 `ΔUST10Y_{t-1}`, `D^freq_t`, 그리고 `include_dS_lag`가 true면 전체 지수의 `ΔS_{t-1}` 하나
  - [ ] 모형 1: β1 (보조 H1, 단측 β1>0), 모형 2: H2 Wald(자유도 3, β_Mac=β_FS=β_Ext=β_Oth), 모형 3: H3 Wald(자유도 2, β2=β3=0)와 H3a(β3≠0, 양측)
  - [ ] 표준오차 HC3, 주 만기 3년물
  - [ ] `audit_korea_context_result.json`의 `pass=false`면 FinStab·External 계수 옆에 해석 유보 표시
  - [ ] 조정 R²는 보고만(근거로 쓰지 않음)
- **완료 기준:** Table 2·3의 모든 칸이 채워지고 H2·H3 Wald 통계량과 p값이 있다. 모형 1이 모형 2의 제약 특수형임을 수치로 확인(토픽 계수를 모두 같게 제약한 모형 2 = 모형 1: 결과가 일치).

### P9. 강건성, 로컬 프로젝션, 그림

- **목적:** R1~R11, 로컬 프로젝션(h=0..10), Figure 1~3, Table 4 (계획서 7.3절, 8절, 9절).
- **선행:** P8. **계획서 절:** 7.3, 8, 9.
- **스크립트:** `scripts/24_robustness.py`, `scripts/25_local_projection.py`, `scripts/26_figures.py`
- **출력**
  - `data/processed/table4_robustness.csv` — `check(R1..R11), model, maturity, term, coef, se, p, n, note`
  - `data/processed/lp_results.csv` — `spec(main|topic_macro_fs), maturity, h, regime(non_inv|inv), coef, ci90_low, ci90_high`
  - `figures/fig1_index_and_rate.png`, `fig2_topic_paths.png`, `fig3_regime_paths.png`
- **작업 목록**
  - [ ] R1 동결 회의(`d_i = 0`), R2 수준 `S_t`, R3 Newey-West, R4 `ΔS×D_{2025+}`, R5 연속 `Spread_{t-1}`(β3<0이 증폭), R6 3차·4차 분리 더미, R7 τ=1(2일 창), R8 정례 외 회의 포함, R9 의사록 공개일 사건 분석(한국어 공개일, 2주 시차 시기), R10 Cook's distance, R11 `ΔS_{t-1}` 추가(본 사양에 이미 포함된 경우 해당 없음 표기)
  - [ ] 로컬 프로젝션: 지평 h마다 OLS 따로, HC3, 90% 신뢰구간, 국면별 `β1(h)`(비역전)와 `β1(h)+β3(h)`(역전). 토픽별 경로(Macro, FinStab)는 탐색적으로 표시
  - [ ] 그림 스타일 결정이 필요하면 `dataviz` 가이드를 따른다
- **완료 기준:** Table 4에 R1~R11 전부 행이 있고(해당 없음은 사유), Figure 1~3이 생성된다. 표본 수가 극히 적은 하위표본(예: R1 동결 회의)은 `n`을 반드시 같이 표시.

### P10. 원고 작성

- **목적:** 계획서 구조에 맞춘 원고 초안과 지도교수 피드백 반영.
- **선행:** P9. **계획서 절:** 9, 10, 11(한계).
- **작업 목록**
  - [ ] 표·그림 번호를 6절 대응표와 일치시키기
  - [ ] 한계(계획서 11절): 감사 결과가 `pass=false`면 해당 한계를 본문 결과 해석 절에 명시
  - [ ] 초안 → 지도교수 피드백 → 최종
- **완료 기준:** 원고의 모든 수치가 `data/processed/`의 표 파일에서 나온다(수작업 입력 수치 0).

---

## 3. 의존성과 차단 요소

### 3.1 의존 관계

```
P1 ──► P2 ──┬──► P4-c ──► P5-d ───────────────┐
            │      ▲                           │
            │      └── P4-a ◄── P4-0           │
            │            ▲                     │
            │       [HF 승인]                  │
            ├──► P5-a ──► P5-b ──► P5-c ──┐    │
            │                              ▼    │
            └─────────────────────────────► P6 ─┼─► [tag index-frozen]
                                                │            │
P3  (독립, 모델 불필요) ────────────────────────┘            │
P7-수집·정리 (독립, 단 병합은 P6 이후) ───────────────────► P8 ──► P9 ──► P10
```

- P3은 P1~P2와 독립이다. 결과(표 65 오기 판단)는 P8 전 Table 1에만 필요하다.
- P7의 수집·정리는 P6과 독립이지만, `scripts/22` 이후는 `index-frozen` tag가 필요하다.
- P5-d는 P4-c의 예측이 필요하다. 그래서 승인 지연은 P5-d → P6(감사 판정은 지수 값을 안 바꾸지만 P8 입력) 순으로 전파된다.

### 3.2 차단 요소별로 막힌 동안 진행할 수 있는 작업

| 차단 요소 | 막히는 작업 | 막힌 동안 진행 가능한 작업 |
|---|---|---|
| WCB 모델 승인 대기 | P4-a/b/c, P5-d, P6 이후 | **P1, P2, P3, P5-0(개발 표본 직접 라벨)·P5-a(LLM 개발 표본 실행, 프롬프트 설계, 전체 라벨링), P5-b(검증 표본 라벨)·P5-c(κ), P7 수집·정리, P4-0 준비** |
| HF 시드 분할 데이터 승인 대기 | P4-b(재현 점검) | 위와 동일. 추론(P4-c)은 분할 데이터 없이 모델만으로 가능 |
| ECOS 키 오류·만료 등 수집 실패 | P7 | P1~P6 전부. 키는 `.env`에 있고 FRED는 키가 필요 없다. P7은 P6 이후 병합이므로 수집 지연이 지수 작업을 막지 않음 |
| OpenAI 크레딧 미충전(D12, 현재 5달러) | P5-a 전체 라벨링(개발 표본 40문장 실행은 소액으로 가능) | P1~P3, **P5-0 개발 표본 직접 라벨**, P7 |
| 사용자 라벨링 시간 부족(D2: 약 10~12시간) | P5-0, P5-b, P5-d, P1·P2 검수 | 계획서가 정한 규모(40 / 120 / 50 / 20문서)는 줄이지 않는다. 일정을 조정하고 우선순위: P5-0 → P1·P2 검수 → P3 → P5-b → P5-d |

---

## 4. 일정 (2026-10-19 월요일 시작)

계획서 10절은 6~8주다. 계획서 1주차 항목(PDF 수집, 회의 마스터, 구조 진단)은 이미 끝났으므로 **계획서 2주차 작업부터** 현재 상태에 맞춰 재배치한다. 날짜는 월요일 기준 주 시작이다. 승인 시점은 불확실하므로 P4가 포함된 주는 승인 시점에 따라 이동한다.

| 주 | 기간 | 작업 | 산출 / 마일스톤 |
|---|---|---|---|
| 1주 | 10/19 ~ 10/23 | P1 구간 추출(시기별 규칙 설계·구현), P3 라벨 방향 감사, P4-0 준비, 승인 상태 확인, **P7 ECOS·FRED 수집 시작** | `discussion_blocks.csv`, `wcb_label_audit.csv` |
| 2주 | 10/26 ~ 10/30 | P1 20문서 검수 완료, P2 문장 분할(`pysbd`)·표결 표시·20문서 검수, **P5-0 개발 표본 40문장 추출·직접 라벨**, P5-a 프롬프트 점검 준비(`--dry-run`), P7 시장 데이터 수집 | `sentences.csv`, `topic_dev_sample.csv`, `table1_label_audit.csv` |
| 3주 | 11/2 ~ 11/6 | P5-a 개발 표본 실행·프롬프트 수정·설정 고정·전체 라벨링(D12 충전 후), P5-b 검증 120문장 직접 라벨, **P4-a·b 재현 점검(승인 시)**, P7 정리 | `sentence_topic.csv`, `table1_repro_f1.csv` |
| 4주 | 11/9 ~ 11/13 | **P4-c 전체 추론(GPU)**, P5-c κ, P5-d 50문장 감사, **P6 지수 산출·ρ1 검정·tag `index-frozen`** | `stance_index.csv`, Table 1 완성 |
| 5주 | 11/16 ~ 11/20 | P8 병합·기술통계·모형 1~3·Wald 검정 | Table 2·3, Figure 1 |
| 6주 | 11/23 ~ 11/27 | P9 강건성 R1~R11, 로컬 프로젝션, Figure 2·3 | Table 4 |
| 7주 | 11/30 ~ 12/4 | P10 초고 | 원고 초안 |
| 8주 | 12/7 ~ 12/11 | 지도교수 피드백 반영(예비 일정) | 최종 원고 |

- **승인 지연 시 일정:** 11/6(금)까지 모델 승인이 안 되면 4주차 이후 전체가 밀린다. 대안 검토는 보류 상태다(5절 D3, 사용자 결정). 그동안 P1~P3, P5 일부, P7이 선행되어 있으므로 승인 후 P4 → P6까지 약 1주로 압축 가능하다(추정).
- 계획서 10절의 4주차 마일스톤("ΔS_t 자기상관 검정으로 ΔS_{t-1} 포함 여부 확정, 금리 데이터 사용 전")은 그대로 유지한다.

---

## 5. 사용자 결정 목록

이전 판의 결정 필요 항목을 반영한 현재 상태다. **결정이 아직 필요한 것은 D3, D12뿐이다.**

| # | 결정 | 상태 | 내용 |
|---|---|---|---|
| D1 | 토픽 라벨링 LLM | **확정** | GPT-6.1 Sol(`gpt-6.1-sol`), OpenAI Responses API 구조화 출력(strict JSON 스키마, 가이드 부록). 추론 강도는 하나로 고정(권장 low), temperature는 지원 시 0. 응답의 `model` 필드·토큰 사용량·원문 응답 저장. 예상 비용 12~20달러(**추정**, 크레딧 충전 필요) |
| D2 | 사람 작업량 | **확정** | 사람 작업 약 10~12시간 + 개발 표본 40문장 |
| D3 | HF 모델·시드 분할 데이터 승인 | **승인 대기** (사용자 결정) | 대안 검토는 보류. 11/6(금)까지 미승인이면 일정 영향(4절) |
| D4 | ECOS API 키 | **완료** | `.env`의 `ECOS_API_KEY` (값은 읽지 않음) |
| D5 | FRED API 키 | **해당 없음** | `fredgraph.csv`로 키 없이 수집 |
| D6 | 한국어 의사록 공개일 | **완료** | 2023.4 이후 28회, `data/metadata/ko_release_dates.csv` |
| D7 | 예비 감사 69문장 | **완료** | 69행 원자료 제공(`data/raw/wcb/wcb_hf_preview_69rows.csv`). 판정 기록은 없으므로 P3 전체 감사로 대체 |
| D8 | 층화 기준 | **확정** | 토픽 검증 120 = LLM 토픽별 30, 시기 비례. 감사 50 = FinStab 25 / External 25, 시기 비례 |
| D9 | 문장 수 적은 회의 | **확정** | 분모 `N_tot − N_irr` 10 미만은 경고만, 제외하지 않음 |
| D10 | 문장 분할기 패키지 | **확정** | `pysbd`를 `uv add`로 추가(P2 시작 시) |
| D11 | 5.3절 감사 대칭 사례 | **확정** | 외환 안정·자본 유입·연준 완화 기대·금리차 축소 → 비둘기. 원래 행과 나누어 집계 |
| **D12** | **OpenAI 크레딧 충전** | **신규, 필요** | 현재 5달러. **P5-a 전체 라벨링 전까지**(일정상 11/2 주). 개발 표본 40문장 실행은 소액으로 가능 |

---

## 6. 산출물 대응표 (계획서 9절)

| 산출물 | 구성 요소 | 단계 | 스크립트 | 파일 |
|---|---|---|---|---|
| **Table 1** 분류와 라벨 품질 | WCB 통합 모델 재현 F1(가중·매크로, 부트스트랩 CI, 논문 0.755 비교) | P4-b | `12_repro_wcb_model.py` | `data/processed/table1_repro_f1.csv` |
| | 토픽 사람–LLM κ(토픽별 이진 + 전체 참고) | P5-c | `16_topic_kappa.py` | `data/processed/table1_topic_kappa.csv` |
| | 감사: 라벨 방향 | P3 | `11_audit_wcb_labels.py` | `data/processed/table1_label_audit.csv` |
| | 감사: 한국 맥락 모델 예측 | P5-d | `17_audit_korea_context.py` | `data/processed/audit_korea_context_result.json` |
| | 감사: 표결 문장 제거·섹션 추출 | P1, P2 | `09_extract_discussion.py`, `10_split_sentences.py` | `data/interim/audit_sections_20.csv`, `audit_votes_20.csv` |
| **Table 2** 기술통계 | 주요 변수, ΔS–Δi 상관, ρ1·검정, 역전·비역전 회의 수, 금리 결정 분포 | P6, P7, P8 | `18b_test_rho1.py`, `22_merge_and_describe.py` | `data/processed/table2_descriptives.csv`, `rho1_test.json` |
| **Table 3** 본 회귀 | 모형 1·2·3 × 3년물·10년물, HC3, H2·H3 Wald, 조정 R², 관측치 수 | P8 | `23_regressions.py` | `data/processed/table3_main_regressions.csv` |
| **Table 4** 강건성 | R1~R11 | P9 | `24_robustness.py` | `data/processed/table4_robustness.csv` |
| **Figure 1** | S_t와 기준금리 시계열, 역전 구간 음영 | P8(그림), P7(역전 구간) | `26_figures.py` | `figures/fig1_index_and_rate.png` |
| **Figure 2** | 토픽별 반응 경로(Macro, FinStab), 탐색적 | P9 | `25_local_projection.py`, `26_figures.py` | `data/processed/lp_results.csv`, `figures/fig2_topic_paths.png` |
| **Figure 3** | 국면별 반응 경로 β1(h) 대 β1(h)+β3(h) | P9 | `25_local_projection.py`, `26_figures.py` | `data/processed/lp_results.csv`, `figures/fig3_regime_paths.png` |

(`figures/` 폴더는 새로 만들며 gitignore 대상이 아니므로 커밋 여부는 결과가 나온 뒤 결정한다.)

---

## 7. 위험과 대응

"계획서"로 표시한 대응은 계획서가 정한 것이고, "결정 필요"는 계획서에 정해진 대응이 없어 사용자 결정이 필요하다.

| 위험 | 신호 | 대응 | 출처 |
|---|---|---|---|
| **섹션 추출 실패** (제목 줄 갈라짐, 로마숫자 분리, 오기, END 앵커 부재) | `section_manual_queue.csv`에 문서가 쌓임 | 제목 1순위 → 문구 앵커 2순위 → 둘 다 실패하면 수작업 목록. 실패 문서를 수동으로 구간 지정해 `extract_method=manual`로 기록. 수작업 비율이 크면 사용자에게 보고 | 계획서 5.1절 + 이 문서 |
| **회의당 문장 수 부족** | 분모 `N_tot − N_irr` < 10인 회의 | 계획서 6.1절: **경고만 하고 표본 유지**, 경고 회의 목록 보고. 위원 토의 전체 사용으로 이미 대응 | 계획서 4.1절, 6.1절, 부록 B |
| **표결 정규식 과잉 제거** | 20문서 검수에서 과잉 제거(`over`) 비율이 높음 | 계획서는 비율 보고만 요구하고 허용 한도를 정하지 않음 → **결정 필요**. 향후 경로·조건부 서술은 표결 문장이 아니다(가이드 C2). `is_vote`를 삭제가 아닌 표시로 두었으므로 규칙을 고쳐도 재추론 없이 P6만 다시 돌리면 된다 | 계획서 5.1절 |
| **표결 정규식 누락** | 검수에서 `missed` 비율이 높음 | 위와 동일, 규칙 보강 후 다른 20문서로 재검수 | 계획서 5.1절 |
| **모델 승인 지연** | 11/6까지 미승인 | 3.2절의 병행 작업 진행. 대안은 **결정 필요**(D3). 부록 B에서 기각한 대안은 쓰지 않음 | 계획서 부록 B |
| **재현 F1이 논문 값과 크게 다름** | P4-b에서 0.755(±0.019)와 격차 | 입력 정규화·라벨 매핑·분할 시드 점검. 통과 기준이 계획서에 없으므로 원인 점검 후 **결정 요청** | 계획서 5.2절 |
| **5.3절 감사 불일치율 30% 이상** | `audit_korea_context_result.json`의 `pass=false` (불일치율 = 불일치/(일치+불일치), 애매 제외) | 모형 2의 FinStab·External 계수 해석을 유보하고 한계로 명시. 라벨 재작성·재학습은 하지 않음 | 계획서 5.3절, 부록 B |
| **토픽 κ < 0.6** | `table1_topic_kappa.csv` | 계획서 5.4절: 미달 토픽을 **Other에 합침**(Other는 합치지 않음). H2 자유도 = 남은 토픽 수 − 1. FinStab·External이 합쳐지면 한국 특화 해석이 약해진다는 점을 결과에 명시 | 계획서 2.1절, 5.4절 |
| **라벨 방향 감사에서 표 65가 오기가 아닌 것으로 확정** | P3 결과가 예비 감사와 반대 | 계획서는 "전체 1,000문장 감사로 확정"이라고만 함. 반대 결과면 이후 처리는 **결정 필요** | 계획서 4.4절 |
| **하방 금융불안 문장 등 WCB 약점** | P5-d에서 불일치 집중 | 5.3절 기준으로 채점·보고. 라벨을 새로 만들지 않는다 | 계획서 5.3절, 부록 B |
| **LLM 호출 실패·거절·비용 초과** | 배치 id 불일치, 누적 비용이 `--max-cost` 도달 | 불일치·거절 배치는 같은 설정으로 1회 재시도 후 수작업 목록. 비용 상한 도달 시 중단하고 사용자 보고(D12) | 가이드 부록 |
| **프롬프트를 검증 표본을 본 뒤 고치고 싶어짐** | κ가 낮은 토픽 발생 | 금지(계획서 5.4절). 고치려면 새 prompt_version으로 개발 표본 단계부터 다시 하고 검증 표본을 새로 뽑는다 → **사용자 결정 필요** | 계획서 5.4절, 가이드 공통 원칙 3 |
| **금리 데이터를 본 뒤 지수 수정** | tag 이후 지수 변경 필요가 생김 | 원칙적으로 금지. 불가피하면 사용자 결정 후 `RUNLOG.md`에 기록, 결과 해석 절에 명시 | 계획서 2.2절 |
| **ρ1 검정 결과가 경계(p≈0.05)** | `rho1_test.json` | 규칙대로 5% 기준을 기계적으로 적용. R11로 다른 쪽도 보고 | 계획서 6.4절 |
| **표본 크기 부족** | 하위표본(R1, 국면별) 유의성 없음 | 한계로 명시(계획서 11절). 하위표본의 `n` 항상 표시 | 계획서 11절 |
| **시장 데이터 정렬 오류**(휴장일, 미국 영업일) | 회의일 `ΔY` 결측·이상치 | P7 완료 기준 (i), 극단값은 R10(Cook's distance)에서 점검 | 계획서 7.1절, 8절 |
| **원자료 변조** | `07_verify_manifest.py` 실패 | 즉시 중단, 불일치 목록 확인 | 이 문서 1.1절 |

---

## 8. 검토 요청

1차 검토 요청(10건 이상)에 대한 현재 상태다. 계획서 갱신본이 반영한 내용은 반영 위치를 적었다. 새로 발견한 의문점은 맨 아래에 별도로 둔다.

| # | 1차 검토 요청 | 상태 | 반영 위치 |
|---|---|---|---|
| 1 | 4.1절 문서 구성 표의 예외(2012-05~12 Ⅳ 없음, 제목 줄 갈라짐 3건, 2023-07-13 번호 오기, 2010~2011 번호 분리) | **해결(계획서 반영)** | 계획서 4.1절 문서 구성 표 아래 "예외" 문단 |
| 2 | 루트에 다른 버전 계획서 없음 | **종결** | — |
| 3 | 2023.4 이후 `section` 구분 불가 | **해결(계획서 반영)** | 계획서 5.1절 (기록용, 분석에는 쓰지 않음). plan.md P1 |
| 4 | ΔS의 "직전 회의", 관측치 161 | **해결(계획서 반영)** | 계획서 6.3절 (직전 정례 회의, 첫 회의 ΔS 없음, 161회). plan.md P6 |
| 5 | 2023-04-11의 ΔS가 문서 형식 변화를 가로지름 | **변경 없음(R10에서 확인)** | 계획서 8절 R10(Cook's distance), 11절·부록 B |
| 6 | `N_tot` 정의 | **해결(계획서 반영)** | 계획서 6.1절 (표결·도입 문장을 뺀 문장 수). plan.md P6 |
| 7 | 5.3절 감사에서 "애매" 처리 | **해결(계획서 반영)** | 계획서 5.3절 (불일치율 = 불일치/(일치+불일치)), 부록 B. plan.md P3·P5-d |
| 8 | 토픽별 κ의 정의 | **해결(계획서 반영)** | 계획서 5.4절 (토픽 대 나머지 이진 κ + 전체 κ 참고) |
| 9 | κ 미달 토픽의 합칠 대상 | **해결(계획서 반영)** | 계획서 5.4절 (Other에 합침), 부록 B |
| 10 | 토픽 합칠 때 H2 자유도 | **해결(계획서 반영)** | 계획서 2.1절, 5.4절 (남은 토픽 수 − 1) |
| 11 | 2026-09-15 공개일 미확인 | **해결(계획서 반영)** | 계획서 4.1절 공개 시차 문단 + `data/metadata/ko_release_dates.csv` (2026-08-27 회의의 한국어 공개일이 2026-09-15임을 직접 확인) |
| 12 | 20문서 검수 표본 | **해결(계획서 반영)** | 계획서 5.5절, 가이드 C (P1·P2는 같은 20문서) |

### 새로 발견한 사항 (본문에는 반영하지 않음)

1. 가이드 A4 예시 11문장의 `rid`는 `final_data.csv` 행 번호(0부터)이고, 문장 본문은 곡선 따옴표(`’`)가 직선(`'`)으로 바뀌어 있어 rid 23, 660은 단순 비교로는 불일치로 나온다. 따옴표를 통일하면 11건 모두 일치한다. 코퍼스(PDF) 문장과 대조할 때도 같은 정규화가 필요하다는 점만 알려 둔다.
2. 한국어 공개일 파일에는 공개 시각이 없다. R9에서 사건일을 t 또는 t+1로 정할 때 필요한 정보인데(계획서 부록 A), 계획서가 이를 단일 규칙으로 고정하지 않았다. R9 단계 전에 규칙이 필요하다.
3. 일정상 P5-b(검증 120)와 P5-d(감사 50)가 다른 주에 있어 사람 작업이 3주차~4주차에 몰린다. 계획서가 정한 규모는 그대로이므로 설계 문제는 아니고 일정 위험으로만 기록한다.
