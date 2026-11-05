---
title: "BOK 의사록 주석 가이드"
version: "v1.3 (2026-11-06)"
applies_to: "연구계획서 5.1·5.3·5.4·5.5절, plan.md P1·P2·P3·P5"
---

# BOK 의사록 주석 가이드 v1.3

변경 이력: v1.0 → v1.1 (2026-10-17) B3에 대칭 사례 추가(연구자 결정 D11), 부록에 LLM 실행 설정(GPT-6.1 Sol, Responses API 구조화 출력) 명시.
v1.1 → v1.2 (2026-10-30) C2에 표결 판정 보완 3건 추가(P2 패턴 조사 후 연구자 결정): 결정+향후 혼합 문장, 이번 회의 표지(조건 B) 없는 구체적 결정 문장, 조건 B 표현 확장.
v1.2 → v1.3 (2026-11-06) C2 보완: 조건 B에 `during the intermeeting period` 추가, 결정 단서에 `resolved`와 `found (it) appropriate/desirable` 추가(연구자 결정, P2 2차 교차 점검 후), "maintain/keep/hold/leave the current level of the Base Rate" 어순을 구체적 결정 (a)에 추가.

이 문서는 사람과 LLM이 **같은 규칙**으로 판정하도록 만든 기준이다. 세 부분으로 나뉜다.

| 부분 | 판정 내용 | 누가 | 어디에 쓰나 |
|---|---|---|---|
| **A. 토픽** | 문장 하나에 토픽 하나 (Macro / FinStab / External / Other) | LLM(전체 문장), 사람(개발 표본 40, 검증 표본 120) | 계획서 5.4절, plan.md P5-0~c |
| **B. 한국 맥락 스탠스 감사** | WCB 라벨·예측의 매파/비둘기 방향이 계획서 5.3절 기준과 맞는지 | 사람 | 계획서 5.3·5.5절, plan.md P3, P5-d |
| **C. 섹션·표결 검수** | 위원 토의 경계, 표결 의견 문장, 도입 문장 표시가 맞는지 | 사람 | 계획서 5.1·5.5절, plan.md P1·P2 (같은 20문서) |

## 공통 원칙

1. **문장 단위로, 그 문장만 보고** 판정한다. 회의 날짜, 앞뒤 문장, 그 시기의 실제 금리 결정은 보지 않는다. LLM에도 문장만 준다.
2. **눈가림(blind):** 사람은 판정할 때 LLM 토픽과 WCB 스탠스 라벨을 보지 않는다. 판정을 다 기록한 뒤에 병합한다.
3. **사전 고정:** 검증 표본(토픽 120문장, 감사 50문장) 판정을 시작한 뒤에는 이 가이드를 고치지 않는다. 고쳐야 하면 버전을 올리고, 이미 한 판정을 새 버전으로 처음부터 다시 한다.
4. **애매 표시:** 규칙을 적용해도 두 판정이 비슷하게 그럴듯하면 판정은 하나 고르고 `ambiguous = 1`로 표시한다. 애매를 피하려고 억지로 확신하지 않는다.
5. 대명사로 시작해 내용이 거의 없는 문장(예: "The member added that this was also the case.")은 문장 안에 있는 내용만으로 판정한다. 내용이 없으면 Other, `ambiguous = 1`.

---

# A. 토픽 판정

## A1. 토픽 정의

| 토픽 | 포함 | 포함하지 않음 (→ 다른 토픽) |
|---|---|---|
| **Macro** (국내 실물·물가) | 소비자물가, 근원물가, 기대인플레이션, 공공요금·농산물·유가·원자재 가격의 **물가 영향**, 성장, 소비, 투자, 수출입과 세계경제·교역 등 **실물** 경기, 고용, 임금, 산출갭, 경기 전망과 실물 불확실성 | 주택 매매가격(→FinStab), 환율·외환시장(→External) |
| **FinStab** (금융안정) | 가계부채·가계대출, 주택 매매가격·거래량·주택담보대출, 부동산 PF, 금융불균형, 레버리지·위험추구, 연체율, 취약차주, 비은행 금융기관 건전성, 신용위험, 기업 부실·구조조정, 국내 신용·자금조달 시장의 경색, 거시건전성 정책(LTV·DSR 등) | 전월세 가격이 **물가 구성요소**로 언급된 경우(→Macro) |
| **External** (대외 금융·정책 여건) | 원/달러 환율과 외환시장 변동성, 자본 유출입·외국인 증권투자, 연준과 주요국 통화정책, 한미 금리차, 글로벌 금융시장 불안·위험회피 | 세계경제 성장·교역·수출(→Macro) |
| **Other** | 통화정책 운영 일반(금리 수준의 적정성 일반론, 정책 여력, 파급경로, 시장과의 소통, 향후 결정 방식), 재정정책·정책 공조 일반, 회의 절차, 위 세 토픽에 들지 않는 문장 | 근거가 명시된 정책 판단(→근거의 토픽, A2 참조) |

## A2. 판정 절차 (순서대로 적용)

1. **경제·정책 내용이 있는가?** 없으면 → Other.
2. **정책 판단이 있는가?** (기준금리 수준, 긴축·완화의 정도, 정책 방향에 대한 의견)
   - 있으면 → 그 판단의 **근거**가 속한 토픽. 근거는 보통 *because, since, as, given, considering, in view of, in light of* 뒤에 나온다.
   - 근거가 여러 개면 가장 길게(비중 있게) 서술된 근거의 토픽. 비슷하면 **먼저 나온 근거**의 토픽을 고르고 `ambiguous = 1`.
   - 근거가 없으면 → Other.
3. **정책 판단이 없는 평가·전망 문장이면** → **주절이 서술하는 대상**의 토픽. *due to, amid, driven by, owing to* 같은 원인 표현은 보조 정보로 보고, 주절의 결과를 기준으로 한다.
   - "CPI fell **due to** lower oil prices" → Macro (결과: 물가)
   - "Exports were sluggish **due to** the global slowdown" → Macro (결과: 수출, 실물)
   - "The won depreciated **amid** expectations of Fed tightening" → External
   - "Housing prices fell **amid** higher lending rates" → FinStab
4. **A3의 경계 규칙**을 적용한다.
5. 그래도 두 토픽이 비슷하면 → **문장에 먼저 나온 토픽**, `ambiguous = 1`.

## A3. 경계 규칙

| 상황 | 판정 |
|---|---|
| 환율이 물가 경로의 **여러 요인 중 하나**로 언급됨 | Macro |
| 환율 자체, 외환시장 안정, 외환 변동성이 주제 | External |
| 세계경제 성장, 교역, 수출 경기 | Macro |
| 주요국 통화정책, 글로벌 금융여건, 자본 흐름 | External |
| 유가·원자재·지정학적 사건이 물가·성장에 주는 영향 | Macro |
| 유가·원자재·지정학적 사건이 금융시장·자본 흐름에 주는 영향 | External |
| 주택 매매가격, 거래, 주택담보대출, PF | FinStab |
| 전월세 가격이 물가 구성요소로 언급됨 | Macro |
| 국내 시장금리·주가가 금융불안·신용위험의 맥락 | FinStab |
| 국내 시장금리가 정책 파급의 맥락(기준금리와의 괴리, 전달 효과) | Other |
| 재정지출이 성장에 미치는 영향 | Macro |
| 거시건전성 정책(LTV·DSR, 대출 규제) | FinStab |
| 정부·중앙은행 정책 공조 일반 | Other |
| 팬데믹의 실물 영향 / 금융시장 영향 | Macro / 해당 금융 토픽 |
| 표결 의견 문장, 도입 문장(원래 라벨링 대상이 아님. 섞여 들어오면) | Other |

## A4. 예시 (LLM few-shot 겸용)

아래 문장은 WCB `final_data.csv`의 행 번호(`rid`, 0부터)다. **이 문장들은 사람 검증 표본(개발 40, 검증 120)에서 제외한다.**

| rid | 문장 (WCB 소문자 원문) | 토픽 | amb | 이유 |
|---|---|---|---|---|
| 32 | members expected cpi to fall somewhat going forward, given recent underlying inflation and the decline in oil prices, and fluctuate in the mid- to upper-1 percent range, not deviating greatly from its target. | Macro | 0 | 물가 전망. 유가는 물가 요인 |
| 56 | members expressed concerns that, on top of the slowdown of domestic demand, the sluggishness of exports that had become apparent since the second quarter might limit domestic economic growth. | Macro | 0 | 수출 부진은 실물 경기 |
| 435 | the future path of inflation is likely to be influenced by international oil prices and exchange rate movements, agricultural product price trends, and whether public utility fees are adjusted. | Macro | 0 | 환율은 물가 요인 중 하나(A3) |
| 295 | the member noted, however, that a sharp correction in housing prices amid rising delinquencies in loans to the real estate sector could lead to an increase in credit risks and to financial market instability. | FinStab | 0 | 주택가격 조정, 연체, 신용위험 |
| 165 | meanwhile, the member presented the opinion that, as loan delinquency rates for real estate project financing and at non-bank financial institutions continued to rise, it would be necessary to examine risks more closely, keeping in mind the possibilities of deterioration in asset quality of related financial institutions, as well as of the weakening of their financial intermediary functions. | FinStab | 0 | PF·비은행 연체 |
| 99 | the member assessed that, since the record high interest rate differential between korea and the u.s. could destabilize exchange rates and expand volatility in the foreign exchange market, it would be important to keep a close eye on foreign exchange movements and prevent any rise in foreign exchange volatility. | External | 0 | 한미 금리차, 외환 변동성 |
| 629 | finally, the member noted that, from the perspective of the balance of payments, korea generally saw sustained net inflows of foreign domestic bond investment funds during the past inversions of the us and korean policy rates, but judged that if the inversion period were to last longer with the interest rate gap widening going forward, it would not be easy to rule out a possibility of some foreign capital outflows. | External | 0 | 금리 역전, 자본 유출 |
| 307 | another member noted that, in view of the factors contributing to the vulnerability of the korean economy, such as the excessive household debt level and low corporate profitability, as a precaution against further expansions of financial unrest in emerging market countries there was a need to thoroughly prepare measures in advance for responding to any sudden reversal of foreign capital flows. | External | 1 | 주장(대비책)의 대상이 자본 유출 반전. 가계부채는 배경(A2-2) |
| 23 | the member stated that after the svb incident, risk aversion sentiment had been strengthened globally and that there were also expectations of an easing of the federal reserve's monetary policy tightening stance. | External | 0 | 글로벌 위험회피, 연준 정책 |
| 660 | the member also noted that, as the effects of the central bank's monetary policy ultimately depended on the behavior of commercial banks that are at the center of monetary policy transmissions, it would be also important to assess the capacity of korean commercial banks to create credit and seek measures to enhance such capacity. | Other | 0 | 정책 파급경로 일반 |
| 31 | the member also noted that the board should decide when to make an additional adjustment to monetary accommodation, while reviewing the transmission effects of the base rate hikes, the developments and impacts of the pandemic, and growth and inflation conditions, while carefully monitoring improvements in financial imbalances at the same time. | Other | 1 | 근거가 여럿이고 비중이 비슷함. 먼저 나온 근거(파급 효과)의 토픽(A2-2) |

---

# B. 한국 맥락 스탠스 감사

## B1. 목적

WCB 라벨(P3) 또는 WCB 모델 예측(P5-d)의 **매파·비둘기 방향**이 계획서 5.3절 기준과 맞는지 **채점**한다. 라벨을 새로 만들거나 고치는 작업이 아니다.

## B2. 절차

1. 문장을 읽고 B3 표의 어느 행에 해당하는지 고른다. 해당하는 행이 없으면 `대상 아님`으로 표시하고 집계에서 뺀다.
2. **WCB 라벨·예측을 보지 않은 상태에서** `expected_direction`(hawkish / dovish)을 기록한다.
3. 기록이 끝난 뒤 WCB 값과 비교해 판정한다.
   - **일치:** 기대 방향과 WCB가 같음
   - **불일치:** 기대 방향과 WCB가 반대이거나, WCB가 neutral·irrelevant인데 B3 기준상 방향이 분명함
   - **애매:** 문장이 방향이 반대인 두 행에 함께 걸림(예: 연체 증가 + 가계대출 반등), 또는 방향성 표현 없이 수준만 서술함
4. **불일치율 = 불일치 / (일치 + 불일치)**. 애매는 분모에서 빼고 개수를 따로 보고한다(계획서 5.3절). P5-d의 통과 기준은 불일치율 30% 미만이다.

## B3. 판정 기준 (계획서 5.3절 표를 풀어 씀)

| 문장 내용 | 기대 방향 | 판단 단서 |
|---|---|---|
| 가계부채·주택가격 **상승**, 금융불균형 **누적**, 레버리지·위험추구 확대 우려 | 매파 | increase, rebound, accumulate, build-up, overheating, risk appetite |
| 위 우려의 **완화** | 비둘기 | slowed, stabilized, eased, contained |
| **하방** 금융불안: 주택가격 급락, 연체 증가, PF 부실, 신용경색, 비은행 유동성 위험 | 비둘기 | sharp correction, delinquency rising, credit crunch, liquidity stress, insolvency |
| 원화 **약세**, 외환시장 불안, 자본 **유출** 우려 | 매파 | depreciation, volatility, outflows |
| 원화 **강세**로 긴축 필요성 감소 | 비둘기 | appreciation, reduced pressure |
| 연준·주요국 **긴축** 압력, 한미 금리차 **확대** 우려 | 매파 | Fed tightening, rate gap widening, inversion prolonged |
| *(대칭)* 외환시장 **안정**, 자본 **유입**, 원화 약세 압력 **완화** | 비둘기 | stabilized FX market, inflows, depreciation pressure eased |
| *(대칭)* 연준·주요국 **완화** 기대, 한미 금리차 **축소**로 대외 제약 완화 | 비둘기 | Fed easing, rate cuts abroad, gap narrowing |

**주의**

- 방향을 판단하려면 "상승/하락", "확대/완화", "우려/해소" 같은 **방향성 표현**이 있어야 한다. 수준만 서술한 문장(예: "the exchange rate stood at around 1,300 won")은 애매로 처리한다.
- *(대칭)* 행은 계획서 5.3절의 행을 반대 방향으로 적용한 것이다(연구자 결정, 2026-10-17). 판정 결과를 보고할 때 원래 행과 대칭 행을 나누어 집계한다.
- 예비 점검에서 WCB 라벨은 하방 금융불안 문장(예: rid 165, 295)을 매파로 붙인 경우가 있었다. 이 사실을 알고 있더라도 **B3 기준대로** 판정한다.

---

# C. 섹션·표결 검수 (P1·P2, 같은 20문서)

## C1. 위원 토의 경계

| 항목 | 확인 내용 |
|---|---|
| 시작 | 경제 상황 토의(2023.2 이전) 또는 단일 토의 섹션(2023.4 이후)의 첫 위원 발언 문장부터 시작하는가 |
| 끝 | 심의 결과(Ⅳ), < Ref > 결정문, 문서 끝 꼬리말 직전에서 끝나는가 |
| 제외 부분 | 개요(참석자 명단), 정부 측 발언(2010~2011년 일부), 심의 결과, 결정문이 남아 있지 않은가 |
| 잔여물 | 각주 문장, 쪽번호, 머리글이 본문에 섞여 있지 않은가. 단어가 하이픈·줄바꿈으로 끊긴 채 남아 있지 않은가 |

기록: `start_ok`, `end_ok`, `leftover_footnote` (0/1), `memo`

## C2. 표결 의견 문장 (`is_vote`)

**정의:** **이번 회의**의 기준금리 결정(인상·인하·동결)에 대한 위원의 찬반 의견 표명, 또는 표결 결과를 서술한 문장.

| 표결 문장이다 (`is_vote = 1`) | 표결 문장이 아니다 (`is_vote = 0`) |
|---|---|
| "it would be desirable to keep the Base Rate at its current level at this meeting" | "further rate hikes may be necessary going forward" (향후 경로) |
| "members agreed unanimously to hold the Base Rate …" | "if inflation persists, additional tightening would be needed" (조건부 미래) |
| "the member argued that the Base Rate should be raised by 25 basis points" | "monetary policy remains restrictive" (정책 기조 평가) |
| 이번 회의 결정 의견과 근거가 한 문장에 함께 있음 ("…keep the Base Rate at 3.50% this time, considering slowing inflation") | 과거 결정에 대한 평가 ("the rate cut last month helped ease…") |

- 향후 경로·조건부 서술은 이 연구가 측정하려는 **결정 이외의 정보**이므로 절대 지우지 않는다.

**기본 규칙 (P2 구현 기준):** 조건 A(기준금리 행동 동사 raise/lower/cut/keep/leave/hold/maintain/freeze 등 + Base Rate)와 조건 B(이번 회의 표지)가 **모두** 있으면 표결 문장이다. 조건 B 없이도 표결 문장인 것: "After the discussions detailed above, … agreed/decided", 실명 소수의견("Mr./Dr./Ms. … dissented / clear opposition / argued for"), "One/Another/To begin, one member proposed / viewed it as appropriate … Base Rate", 2023.4 이후 첫머리 "The majority of / All / A majority of members … Base Rate …, while/Meanwhile … argued for". 향후(going forward), 추가(further, additional), future, if 조건문만 있고 조건 B가 없는 문장은 표결 문장이 아니다.

**v1.2 보완 (연구자 결정, 2026-10-30):**

1. **결정+향후 혼합 문장:** 조건 A+B가 있으면 향후 경로 표현이 한 문장에 섞여 있어도 **표결 문장(`is_vote = 1`)**으로 본다(기본 규칙 그대로). 예: "…it would be appropriate to leave the Base Rate unchanged at the current 3.50% at this meeting and judge whether the Base Rate needs to rise further … going forward." 조건 B가 없는 향후 서술 문장은 표결 문장이 아니다.
2. **조건 B 없는 구체적 결정 문장:** 다음 (a)와 (b)를 **모두** 만족할 때만 표결 문장이다. 하나라도 어긋나면 표결 문장이 아니다.
   - (a) 구체적인 이번 결정이 명시됨: "by N bp / by 0.25 percentage points", "to X%", "at its current (X%) level", "unchanged / on hold at the current level"
   - (b) 향후 표현이 없음: going forward, further(인하·인상의 추가를 뜻할 때), in the future, next meeting(s), if/should 조건문
   - 예(표결): "…the member deemed it appropriate to cut the Base Rate by 25bp." / "…the member took the view that it would be desirable to keep the Base Rate at its current 1.75% level."
3. **조건 B 표현 확장:** 조건 B에 for / in / at this meeting, for the ensuing month를 추가한다(기존: at this/the present/current meeting, this month, this time, for the intermeeting period, **v1.3: during the intermeeting period**, until the next (MPB) meeting). "for now"는 조건 B가 아니다.
4. **표현 확장 (P2 교차 점검 후, 연구자 결정 2026-10-30):** 기준금리 행동 표현에 adjust / upward·downward adjustment, 수치 표현에 "by 0.25 of a percentage point", 결정 단서에 agreed / decided / resolution / judged / deemed, "After the (detailed) discussions … above, … agreed/decided" 변형을 포함한다. **v1.3 추가:** 결정 단서에 `resolved`("After the (detailed) discussions … above, … resolved …" 변형 포함)와 `found (it) appropriate/desirable`을 넣는다. `found`는 단독으로 표결 표지가 아니다. 조건 A(기준금리 행동 + Base Rate)가 있고, 조건 B가 있거나 위 2의 (a) 구체적 결정과 (b) 문장 전체에 향후 표현 없음을 만족할 때만 표결 문장이다. 또 (a)에 "to maintain/keep/hold/leave the current level of the Base Rate" 어순을 추가한다("while maintaining …" 같은 부대 서술은 제외). 조건 B 없는 구체적 결정 문장(위 2)의 (b)는 문장 **전체**에서 향후 표현을 검사한다(근거 절의 "future" 등도 포함).
5. **구체적 수치 없는 개별 위원 의견:** "One/Another member … (opinion/view) … rate should be raised/cut/kept" 형태는 수치와 조건 B가 없어도 표결 문장이다.

## C3. 도입 문장 (`is_boilerplate`)

정해진 문구로, 위원의 판단을 담지 않은 문장. 예: "After hearing staff briefings on …, the discussions among members covered the following areas:", "The MPB members' discussions concerning a change in the Bank of Korea Base Rate were as follows:"

## C4. 기록

P2 검수 표의 `reviewer_judgment`: `ok`(맞게 표시) / `missed`(표결·도입 문장인데 표시 안 됨) / `over`(표결·도입 문장이 아닌데 표시됨)

---

# 부록. LLM 토픽 라벨링 프롬프트 (prompt_version = topic-v1.0)

LLM은 **A(토픽)만** 담당한다. B와 C는 사람만 한다.

| 항목 | 설정 |
|---|---|
| 모델 | GPT-6.1 Sol (`gpt-6.1-sol`). 실제 응답의 `model` 필드(스냅샷 이름)를 매 호출 저장한다 |
| API | OpenAI Responses API, 구조화 출력(`text.format`: `json_schema`, `strict: true`) 또는 SDK `client.responses.parse(text_format=<Pydantic 모델>)` |
| 추론 강도 | 하나로 고정(권장 `low`)하고 기록한다. 개발 표본 점검 뒤에는 바꾸지 않는다 |
| temperature | 모델이 지원하면 0, 지원하지 않으면 설정하지 않고 그 사실을 기록한다 |
| 입력 | 한 번에 20문장, 각 문장에 `id`. 원문(`sent_raw`) 그대로. 날짜·회의 정보는 주지 않는다 |
| 저장 | 요청·응답 원문 전체(JSON), 응답 `id`, 사용 토큰(추론 토큰 포함), 거절(refusal) 여부 |
| 검사 | 입력 id와 출력 id가 1:1인지 확인한다. 누락·중복·거절이 나온 배치는 같은 설정으로 한 번만 다시 호출하고, 그래도 실패하면 수작업 목록으로 보낸다 |
| 재현성 점검 | 개발 표본 40문장을 같은 설정으로 두 번 돌려 일치율을 보고한다 |

**출력 스키마 (strict)**

```json
{
  "type": "object",
  "properties": {
    "labels": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "topic": {"type": "string", "enum": ["Macro", "FinStab", "External", "Other"]},
          "ambiguous": {"type": "integer", "enum": [0, 1]},
          "reason": {"type": "string"}
        },
        "required": ["id", "topic", "ambiguous", "reason"],
        "additionalProperties": false
      }
    }
  },
  "required": ["labels"],
  "additionalProperties": false
}
```

**프롬프트 본문**

```text
[SYSTEM]
You annotate sentences from the English minutes of the Bank of Korea Monetary Policy Board.
For each sentence, assign exactly ONE topic: Macro, FinStab, External, or Other.
Judge each sentence on its own. Do not use outside knowledge about dates or actual policy decisions.

TOPIC DEFINITIONS
- Macro: domestic real economy and prices — CPI, core and expected inflation; effects of public utility fees,
  agricultural, oil and commodity prices ON INFLATION; growth, consumption, investment; exports, imports,
  global growth and trade (real side); employment, wages, output gap; real-economy outlook and uncertainty.
- FinStab: financial stability — household debt and household lending; housing sale prices, transactions,
  mortgage lending; real estate project financing (PF); financial imbalances, leverage, risk-taking;
  delinquency rates, vulnerable borrowers, non-bank soundness, credit risk; corporate distress and
  restructuring; domestic credit or funding market stress; macroprudential policy (LTV, DSR, lending rules).
- External: external financial and policy conditions — KRW/USD exchange rate and FX market volatility;
  capital flows and foreign portfolio investment; the Federal Reserve and other major central banks' policy;
  the Korea–US policy rate differential; global financial market turmoil and risk aversion.
- Other: monetary policy operation in general (appropriateness of the rate level in general, policy room,
  transmission, communication, how future decisions will be made); fiscal policy or policy coordination in
  general; procedural sentences; anything that fits none of the above.

PROCEDURE (apply in order)
1. No economic or policy content -> Other.
2. If the sentence states a POLICY JUDGMENT (rate level, degree of tightening/easing, policy direction),
   label the topic of its JUSTIFICATION (after "because/since/as/given/considering/in view of/in light of").
   Several justifications -> the most elaborated one; if similar, the first one and set ambiguous=1.
   No justification -> Other.
3. If it is an ASSESSMENT or OUTLOOK without a policy judgment, label the topic of what the MAIN CLAUSE
   describes. Causes introduced by "due to/amid/driven by/owing to" are secondary.
4. Boundary rules:
   - Exchange rate mentioned as one of several inflation drivers -> Macro; FX itself or FX stability -> External.
   - Global growth, trade, exports -> Macro; major central banks, global financial conditions, capital flows -> External.
   - Oil/commodity/geopolitical effects on prices or growth -> Macro; on financial markets or capital flows -> External.
   - Housing sale prices, mortgages, PF -> FinStab; rents as a component of inflation -> Macro.
   - Domestic market rates or stock prices in a financial-stress context -> FinStab; in a policy-transmission context -> Other.
   - Fiscal spending effect on growth -> Macro; macroprudential rules -> FinStab; general policy coordination -> Other.
5. If two topics remain equally plausible, choose the one that appears first and set ambiguous=1.

OUTPUT
Return one entry per input id, in input order, following the provided JSON schema.
Keep "reason" to 15 words or fewer.

[EXAMPLES]
(가이드 A4의 예시 11개를 "id / sentence / topic / ambiguous / reason" 형식으로 넣는다)

[USER]
Label these sentences:
{"sentences": [{"id": "...", "text": "..."}, ...]}
```
