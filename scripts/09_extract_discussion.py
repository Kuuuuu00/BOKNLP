"""위원 토의 범위 추출 (plan.md P1, 계획서 4.1·5.1절, 주석 가이드 C).

모드
  --headings  : 163개 PDF의 섹션 제목 후보를 모아 heading_variants.csv 작성 (규칙을 정하기 전 단계)
  --diagnose  : 문서별 글자 크기 분포를 font_size_report.csv에 기록
  (기본)      : 위원 토의 구간 추출 -> discussion_blocks.csv, section_manual_queue.csv,
                discussion_txt/*.txt, 자동 점검 파일, 검수 표본 파일

실행(저장소 루트에서):
  uv run python scripts/09_extract_discussion.py --headings
  uv run python scripts/09_extract_discussion.py --diagnose
  uv run python scripts/09_extract_discussion.py
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pymupdf

# ---------------------------------------------------------------------------
# 제목 패턴 상수 (data/interim/heading_variants.csv 근거로 확정, 163개 문서 전체에서 점검).
# strip_marks()로 정규화한 제목(소문자, 로마숫자·줄끝 각주번호 제거)에 fullmatch로 적용한다.
# ---------------------------------------------------------------------------
HEADING_PATTERNS = {
    # 경제 상황 토의 (2010~2023.2)
    "econ": [
        r"(summary of )?discussions? (on|of) (the )?(current )?economic situation( \(summary\))?",
        r"discussions? related to economic developments( \(summary\))?",  # 2010-01-08
    ],
    # 통화정책 결정 토의 (2010~2023.2) 및 단일 토의 섹션 (2023.4~)
    "policy": [
        r"(summary of )?discussions? (concerning|related to) (the )?monetary policy decision( \(summary\))?",
    ],
    # 제외 섹션
    "gov": [r"remarks by (the )?government representative.*"],
    "delib": [r"results of (the )?deliberation (on|of) monetary policy directions?"],
    "decision": [r"monetary policy decision"],  # 결정문 제목 (< Ref > 아래)
    "outline": [r"outline"],
}
# 제목을 못 찾았을 때 쓰는 2순위 문구 앵커 (줄 단위, 소문자)
START_ANCHORS = {
    "policy": [
        r"discussions? (on|concerning|related to) (changes? in|a change in) the bank of korea base rate were as follows",
        r"discussions? (on|concerning|related to) (changes? in|a change in) the base rate were as follows",
    ],
    "econ": [r"after hearing staff briefings on .*economic"],
}
END_ANCHORS = [r"^<\s*ref\s*>$", r"^after the discussions detailed above"]

# 본문보다 이 값(pt) 이상 작은 span을 각주로 본다 (시기별로 다르면 여기서 지정; --diagnose 결과 참고)
FOOTNOTE_GAP = {"2010-2011": 1.0, "2012-2023.2": 1.0, "2023.4+": 1.0}

ROMAN_CHARS = "ⅠⅡⅢⅣⅤⅥ"
ROMAN_RE = re.compile(rf"^\s*(?:[{ROMAN_CHARS}]\s*[.\s]|(?:VI|IV|V|I{{1,3}})\.)\s*")
PAGE_NO_RE = re.compile(r"^\s*(?:[-–—]\s*\d+\s*[-–—]|\d+)\s*$")
BULLET_RE = re.compile(r"^\s*[□○●■▪•·\-–]\s+")


# ---------------------------------------------------------------------------
# 줄 복원
# ---------------------------------------------------------------------------
class Line:
    __slots__ = ("page", "x0", "x1", "y0", "y1", "size", "bold", "text", "removed")

    def __init__(self, page, x0, x1, y0, y1, size, bold, text, removed=""):
        self.page, self.x0, self.x1, self.y0, self.y1 = page, x0, x1, y0, y1
        self.size, self.bold, self.text, self.removed = size, bold, text, removed


def body_size(doc):
    """글자 수로 가중한 span 크기의 최빈값."""
    c = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    n = len(s["text"].strip())
                    if n:
                        c[round(s["size"], 1)] += n
    return c.most_common(1)[0][0] if c else 0.0, c


def page_lines(page, pno, body, foot_gap):
    """한 쪽의 span을 읽어 줄로 묶는다. 본문보다 foot_gap(pt) 이상 작은 span은 각주로 보고 제거."""
    spans, removed_spans = [], []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if not s["text"].strip():
                    spans.append(s)  # 공백 span은 유지 (단어 사이)
                    continue
                if s["size"] <= body - foot_gap:
                    removed_spans.append(s)
                else:
                    spans.append(s)
    # y 중심이 가까운 span을 같은 줄로 (로마숫자와 제목이 다른 줄로 갈라진 경우 포함)
    items = []
    for s in spans:
        x0, y0, x1, y1 = s["bbox"]
        items.append((s, (y0 + y1) / 2))
    items.sort(key=lambda t: t[1])
    groups = []
    for s, yc in items:
        if groups and abs(yc - groups[-1]["yc"]) < 0.5 * max(s["size"], groups[-1]["size"]):
            g = groups[-1]
            g["spans"].append(s)
            g["yc"] = (g["yc"] * (len(g["spans"]) - 1) + yc) / len(g["spans"])
            g["size"] = max(g["size"], s["size"])
        else:
            groups.append({"spans": [s], "yc": yc, "size": s["size"]})
    lines = []
    for g in groups:
        sp = sorted(g["spans"], key=lambda s: s["bbox"][0])
        parts, prev_x1 = [], None
        for s in sp:
            t = s["text"]
            if prev_x1 is not None and s["bbox"][0] - prev_x1 > 2.5 and parts and not parts[-1].endswith(" ") and not t.startswith(" "):
                parts.append(" ")
            parts.append(t)
            prev_x1 = s["bbox"][2]
        text = re.sub(r"[ \t]+", " ", "".join(parts)).strip()
        if not text:
            continue
        real = [s for s in sp if s["text"].strip()]
        sizes = Counter()
        for s in real:
            sizes[round(s["size"], 1)] += len(s["text"].strip())
        size = sizes.most_common(1)[0][0]
        bold = sum(len(s["text"].strip()) for s in real if s["flags"] & 16 or "bold" in s["font"].lower()) > 0.5 * sum(len(s["text"].strip()) for s in real)
        lines.append(Line(pno, min(s["bbox"][0] for s in sp), max(s["bbox"][2] for s in sp),
                          min(s["bbox"][1] for s in sp), max(s["bbox"][3] for s in sp), size, bold, text))
    # 제거된 각주 span을 줄 단위로 모은다
    rem_items = sorted(((s, (s["bbox"][1] + s["bbox"][3]) / 2) for s in removed_spans), key=lambda t: t[1])
    rem_groups = []
    for s, yc in rem_items:
        if rem_groups and abs(yc - rem_groups[-1][0]) < 0.6 * s["size"]:
            rem_groups[-1][1].append(s)
        else:
            rem_groups.append([yc, [s]])
    removed_lines = []
    for yc, sp in rem_groups:
        sp.sort(key=lambda s: s["bbox"][0])
        parts, prev_x1 = [], None
        for s in sp:
            if prev_x1 is not None and s["bbox"][0] - prev_x1 > 1.5 and parts and not parts[-1].endswith(" ") and not s["text"].startswith(" "):
                parts.append(" ")
            parts.append(s["text"])
            prev_x1 = s["bbox"][2]
        txt = re.sub(r"\s+", " ", "".join(parts)).strip()
        if txt:
            removed_lines.append((pno, txt, sp[0]["bbox"][1], round(max(s["size"] for s in sp), 1)))
    return lines, removed_lines


def repeated_edge_texts(all_lines, page_h, min_pages=3, band=0.09):
    """쪽 위/아래 가장자리 띠에서 숫자를 #으로 바꿔 3쪽 이상 반복되는 줄 문구."""
    cnt = defaultdict(set)
    for ln in all_lines:
        if ln.y1 < page_h * band or ln.y0 > page_h * (1 - band):
            cnt[re.sub(r"\d+", "#", ln.text)].add(ln.page)
    return {k for k, v in cnt.items() if len(v) >= min_pages}


def load_doc(path, foot_gap=1.0):
    """PDF -> (줄 목록, 제거된 각주 목록, 본문 크기, 제거된 머리글·꼬리말 문구)."""
    doc = pymupdf.open(path)
    body, _ = body_size(doc)
    lines, removed = [], []
    page_h = doc[0].rect.height
    for i, page in enumerate(doc, 1):
        ls, rm = page_lines(page, i, body, foot_gap)
        lines.extend(ls)
        removed.extend(rm)
    edges = repeated_edge_texts(lines, page_h)
    keep, edge_removed = [], []
    for ln in lines:
        near_edge = ln.y1 < page_h * 0.09 or ln.y0 > page_h * 0.91
        norm = re.sub(r"\d+", "#", ln.text)
        if PAGE_NO_RE.match(ln.text) or (near_edge and norm in edges):
            edge_removed.append((ln.page, ln.text))
            continue
        keep.append(ln)
    npages = len(doc)
    doc.close()
    return keep, removed, body, edge_removed, npages


# ---------------------------------------------------------------------------
# 제목 후보
# ---------------------------------------------------------------------------
def strip_marks(text):
    """제목 정규화: 줄 끝 각주 번호, 로마숫자, 마침표, 괄호 속 (Summary) 앞뒤 공백 정리."""
    t = text.strip()
    t = re.sub(r"\s*\d{1,2}\)\s*$", "", t)  # 줄 끝 각주 번호 "2)"
    t = re.sub(r"(?<=[A-Za-z\)])\d{1,2}\)?$", "", t)  # "Situation2)" 형태 (공백 없이 붙은 각주)
    t = ROMAN_RE.sub("", t, count=1) if ROMAN_RE.match(t) else re.sub(r"^\s*\.\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip(" .:").lower()
    return t


def heading_candidates(lines, body):
    """로마숫자로 시작하거나, 본문보다 크거나 굵은 짧은 줄. 번호만 있는 줄·제목이 이어진 줄은 합친다."""
    cands = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        starts_roman = bool(ROMAN_RE.match(ln.text)) or bool(re.match(rf"^\s*\.\s+\S", ln.text) and ln.size > body)
        big = (ln.size >= body + 1 or ln.bold) and len(ln.text) <= 110
        if starts_roman or big:
            text, last = ln.text, ln
            j = i + 1
            # 번호만 있는 줄("Ⅲ.") 다음 줄 또는 같은 크기·굵기로 이어지는 줄을 합친다
            while j < n:
                nx = lines[j]
                if nx.page != last.page:
                    break
                only_num = bool(re.fullmatch(rf"\s*(?:[{ROMAN_CHARS}]|VI|IV|V|I{{1,3}})\s*\.?\s*", text))
                same_style = abs(nx.size - last.size) < 0.6 and nx.bold == last.bold and (nx.y0 - last.y1) < 0.8 * last.size
                nx_roman = bool(ROMAN_RE.match(nx.text))
                if (only_num or (same_style and not nx_roman and (ln.size >= body + 1 or ln.bold))) and len(text) < 160:
                    text = text + " " + nx.text
                    last = nx
                    j += 1
                else:
                    break
            cands.append((ln.page, ln.size, ln.bold, text.strip(), i, j - 1))
            i = j
        else:
            i += 1
    return cands


# ---------------------------------------------------------------------------
def era_of(date):
    if date < "2012-01-01":
        return "2010-2011"
    if date < "2023-03-01":
        return "2012-2023.2"
    return "2023.4+"


def pdf_list(pdf_dir):
    return sorted(Path(pdf_dir).glob("bok_minutes_*.pdf"))


def date_of(path):
    return path.stem.replace("bok_minutes_", "")


def run_headings(args):
    rows = []
    for f in pdf_list(args.pdf):
        d = date_of(f)
        lines, removed, body, _, _ = load_doc(f)
        for page, size, bold, text, _, _ in heading_candidates(lines, body):
            rows.append({"meeting_date": d, "era": era_of(d), "page": page, "size": size, "bold": int(bold),
                         "body_size": body, "raw": text, "norm": strip_marks(text)})
    raw = pd.DataFrame(rows)
    raw.to_csv(Path(args.interim) / "heading_candidates_raw.csv", index=False, encoding="utf-8-sig")
    g = raw.groupby("norm").agg(n_docs=("meeting_date", "nunique"), first=("meeting_date", "min"),
                                last=("meeting_date", "max"),
                                eras=("era", lambda s: ",".join(sorted(set(s)))),
                                example=("raw", "first")).reset_index().sort_values("n_docs", ascending=False)
    g.to_csv(Path(args.interim) / "heading_variants.csv", index=False, encoding="utf-8-sig")
    print(f"제목 후보 {len(raw)}줄, 정규화 문구 {len(g)}종 -> heading_variants.csv")


def run_diagnose(args):
    rows = []
    for f in pdf_list(args.pdf):
        d = date_of(f)
        doc = pymupdf.open(f)
        body, c = body_size(doc)
        tot = sum(c.values())
        small = {k: v for k, v in c.items() if k <= body - 1.0}
        large = {k: v for k, v in c.items() if k >= body + 1.0}
        rows.append({"meeting_date": d, "era": era_of(d), "body_size": body,
                     "body_share": round(c[body] / tot, 3),
                     "smaller_sizes": ";".join(f"{k}:{v}" for k, v in sorted(small.items())),
                     "larger_sizes": ";".join(f"{k}:{v}" for k, v in sorted(large.items())),
                     "n_chars_smaller": sum(small.values())})
        doc.close()
    pd.DataFrame(rows).to_csv(Path(args.interim) / "font_size_report.csv", index=False, encoding="utf-8-sig")
    print("font_size_report.csv 작성")


# ---------------------------------------------------------------------------
# 추출
# ---------------------------------------------------------------------------
SPECIAL_CASES = {
    "2023-07-13": "두 번째 제목 번호가 Ⅰ.로 오기",
    "2013-04-11": "Ⅲ 제목이 줄로 갈라짐",
    "2016-03-10": "Ⅲ 제목이 줄로 갈라짐",
    "2019-02-28": "Ⅲ 제목이 줄로 갈라짐",
    "2020-03-16": "긴급회의 (R8용)",
}
for _d in ["2012-05-10", "2012-06-08", "2012-07-12", "2012-08-09", "2012-09-13", "2012-10-11", "2012-11-09", "2012-12-13"]:
    SPECIAL_CASES[_d] = "2012-05~12: Ⅳ(심의 결과) 없음"

EXCLUDED_ROLES = ("outline", "gov", "delib", "decision", "ref", "other_roman")
FORBIDDEN_ANY = {"members_present": r"members present", "not_official": r"not an official document"}
FORBIDDEN_PARA = {  # 문단이 이 제목으로 시작하는 경우 (본문 속 일반 문장은 제외)
    "results_of_deliberation": r"^results of (the )?deliberation",
    "ref": r"^<\s*ref\s*>",
    "mpd_title": r"^monetary policy decision\b(?!\s+(was|is|had|has|would|will|to|in|at|and|that))",
    "remarks_by": r"^remarks by\b",
    "outline": r"^outline\b",
}


def classify(norm):
    for role, pats in HEADING_PATTERNS.items():
        if any(re.fullmatch(p, norm) for p in pats):
            return role
    return None


def find_boundaries(lines, body):
    bs = []
    for page, size, bold, text, i, j in heading_candidates(lines, body):
        role = classify(strip_marks(text))
        if role is None and ROMAN_RE.match(text):
            role = "other_roman"
        if role:
            bs.append({"i": i, "j": j, "role": role, "text": text, "page": page})
    for k, ln in enumerate(lines):
        if re.match(r"^<\s*ref\s*>$", ln.text.lower()):
            bs.append({"i": k, "j": k, "role": "ref", "text": ln.text, "page": ln.page})
    bs.sort(key=lambda b: (b["i"], b["j"]))
    return bs


def build_vocab(docs):
    v = set()
    for d in docs:
        prev_hy = False
        for ln in d["lines"]:
            toks = re.findall(r"[A-Za-z]+", ln.text)
            if prev_hy and toks:
                toks = toks[1:]
            hy = ln.text.endswith("-")
            if hy and toks:
                toks = toks[:-1]
            prev_hy = hy
            v.update(t.lower() for t in toks)
    return v


def append_text(par, txt, vocab):
    if not par:
        return txt
    m = re.search(r"([A-Za-z]+)-$", par)
    if m:
        w = re.match(r"[A-Za-z]+", txt)
        if w and (m.group(1) + w.group(0)).lower() in vocab:
            return par[:-1] + txt  # 하이픈 없이 어휘에 있음 -> 하이픈 제거
        return par + txt  # 진짜 하이픈 복합어 -> 하이픈 유지
    return par + " " + txt


def build_paragraphs(blines, vocab):
    if not blines:
        return []
    margin = Counter(round(l.x0) for l in blines).most_common(1)[0][0]
    gaps = [b.y0 - a.y1 for a, b in zip(blines, blines[1:]) if a.page == b.page]
    med_gap = sorted(gaps)[len(gaps) // 2] if gaps else 0
    paras, cur, prev = [], "", None
    for ln in blines:
        txt = ln.text.replace(" ", " ")
        bullet = bool(BULLET_RE.match(txt))
        if bullet:
            txt = BULLET_RE.sub("", txt, count=1)
        new = (prev is None or bullet or (ln.x0 - margin) > 8
               or (prev.page == ln.page and (ln.y0 - prev.y1) > med_gap + 8))
        if new and cur:
            paras.append(cur)
            cur = ""
        cur = append_text(cur, txt.strip(), vocab)
        prev = ln
    if cur:
        paras.append(cur)
    return [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]


def extract_doc(d, vocab):
    lines, date = d["lines"], d["date"]
    era = era_of(date)
    bs = find_boundaries(lines, d["body"])
    flags, blocks = [], []
    roles = [b["role"] for b in bs]

    def first(role):
        for b in bs:
            if b["role"] == role:
                return b
        return None

    def anchor_idx(pats):
        for k in range(len(lines)):
            if any(re.search(p, lines[k].text.lower()) for p in pats):
                return k
        return None

    def end_for(start_idx, kind):
        for b in bs:
            if b["i"] >= start_idx:
                return b["i"], b["role"]
        if era != "2023.4+":
            for kk in range(start_idx, len(lines)):
                if any(re.search(p, lines[kk].text.lower()) for p in END_ANCHORS):
                    return kk, "anchor"
            flags.append(f"{kind}:end_doc_end")
        return len(lines), "doc_end"

    for kind in ("econ", "policy"):
        b = first(kind)
        if b is not None:
            s, how, start_rule = b["j"] + 1, "title", b["text"]
        else:
            ai = anchor_idx(START_ANCHORS[kind])
            if ai is None:
                continue
            s, how, start_rule = ai, "anchor", "anchor:" + START_ANCHORS[kind][0][:40]
        e, end_rule = end_for(s, kind)
        blines = lines[s:e]
        if not blines:
            continue
        section = "discussion" if (kind == "policy" and era == "2023.4+") else kind
        paras = build_paragraphs(blines, vocab)
        # 2012-05~2013-02: 정부 측 발언이 제목 없이 토의 끝에 붙어 있다 -> 해당 문단부터 블록 끝까지 제외
        excluded = []
        for ix, para in enumerate(paras):
            lp = para.lower()
            if "government representative" in lp and re.search(r"following comments|left the room", lp):
                excluded, paras = paras[ix:], paras[:ix]
                end_rule = "gov_inline"
                flags.append(f"{kind}:gov_inline_removed({len(excluded)}paras)")
                break
        blocks.append({"meeting_date": date, "block_id": f"{date}_{section}", "section": section,
                       "page_start": blines[0].page, "page_end": blines[-1].page,
                       "text_raw": "\n\n".join(paras), "paras": paras,
                       "excluded_paras": excluded, "extract_method": how,
                       "start_rule": start_rule, "end_rule": end_rule,
                       "n_chars": sum(len(p) for p in paras),
                       "flag": ";".join(f for f in flags if f.startswith(kind))})
    unknown = [b["text"] for b in bs if b["role"] == "other_roman"]
    return {"date": date, "era": era, "blocks": blocks, "boundaries": bs, "roles": roles,
            "unknown_roman": unknown}


def load_all(args):
    docs = []
    for f in pdf_list(args.pdf):
        d = date_of(f)
        lines, removed, body, edge_removed, npages = load_doc(f, FOOTNOTE_GAP[era_of(d)])
        docs.append({"date": d, "lines": lines, "removed": removed, "body": body,
                     "edge_removed": edge_removed, "npages": npages})
    return docs


def run_extract(args):
    import random
    interim = Path(args.interim)
    txt_dir = interim / "discussion_txt"
    txt_dir.mkdir(parents=True, exist_ok=True)
    docs = load_all(args)
    vocab = build_vocab(docs)
    print(f"문서 {len(docs)}개 로드, 어휘 {len(vocab)}개")
    results, rows, queue, short = {}, [], [], []
    for d in docs:
        r = extract_doc(d, vocab)
        results[d["date"]] = r
        kinds = {b["section"] for b in r["blocks"]}
        if not (kinds & {"policy", "discussion"}):
            queue.append({"meeting_date": d["date"], "reason": "no_policy_block", "detail": "제목·앵커 모두 실패"})
        if r["era"] != "2023.4+" and "econ" not in kinds and d["date"] != "2020-03-16":
            queue.append({"meeting_date": d["date"], "reason": "no_econ_block", "detail": "제목·앵커 모두 실패"})
        for b in r["blocks"]:
            if b["n_chars"] < 1500:
                short.append({"meeting_date": d["date"], "section": b["section"], "n_chars": b["n_chars"]})
            rows.append({k: v for k, v in b.items() if k not in ("paras", "excluded_paras")})
        out, pages_used = [], set()
        for b in r["blocks"]:
            out.append(f"=== SECTION: {b['section']} ===")
            out.extend(p + "\n" for p in b["paras"])
            pages_used.update(range(b["page_start"], b["page_end"] + 1))
        for b in r["blocks"]:
            if b["excluded_paras"]:
                out.append(f"=== EXCLUDED GOVERNMENT REMARKS (inline, {b['section']}) ===")
                out.extend(p + "\n" for p in b["excluded_paras"])
        out.append("=== REMOVED FOOTNOTES ===")
        for pno, text, y, size in d["removed"]:
            if pno in pages_used and not PAGE_NO_RE.match(text):
                out.append(f"[p{pno}, {size}pt] {text}")
        (txt_dir / f"bok_minutes_{d['date']}.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(interim / "discussion_blocks.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(queue, columns=["meeting_date", "reason", "detail"]).to_csv(
        interim / "section_manual_queue.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(short, columns=["meeting_date", "section", "n_chars"]).to_csv(
        interim / "short_blocks.csv", index=False, encoding="utf-8-sig")
    print(f"블록 {len(rows)}개, 수작업 대기열 {len(queue)}건, 짧은 블록(<1500자, 정보용) {len(short)}건")

    # ---- 자동 점검 ----
    master = pd.read_csv("data/metadata/meeting_master.csv")[["meeting_date", "wcb_num_sentences"]]
    chk = []
    for d in docs:
        r = results[d["date"]]
        paras = [p for b in r["blocks"] for p in b["paras"]]
        full = "\n".join(paras)
        row = {"meeting_date": d["date"], "era": r["era"], "n_chars": len(full),
               "methods": ",".join(sorted({b["extract_method"] for b in r["blocks"]})),
               "sections": ",".join(b["section"] for b in r["blocks"]),
               "unknown_roman": " | ".join(r["unknown_roman"])}
        for k, rx in FORBIDDEN_ANY.items():
            row[k] = len(re.findall(rx, full, flags=re.I))
        for k, rx in FORBIDDEN_PARA.items():
            row[k] = sum(1 for p in paras if re.search(rx, p.lower()))
        row["removed_fn_lines_all_pages"] = sum(1 for _, tx, _, _ in d["removed"] if not PAGE_NO_RE.match(tx))
        row["attached_fn_marker"] = len(re.findall(r"[A-Za-z]\d{1,2}\)(?=\s|$)", full))
        chk.append(row)
    chk = pd.DataFrame(chk).merge(master, on="meeting_date", how="left")
    chk["chars_per_sent"] = chk.n_chars / chk.wcb_num_sentences
    med = chk.groupby("era").chars_per_sent.transform("median")
    chk["ratio_to_era_median"] = (chk.chars_per_sent / med).round(2)
    chk["outlier"] = (chk.ratio_to_era_median < 0.5) | (chk.ratio_to_era_median > 2.0)
    sub = chk.dropna(subset=["wcb_num_sentences"])
    corr = sub.n_chars.corr(sub.wcb_num_sentences)
    chk.to_csv(interim / "extract_checks.csv", index=False, encoding="utf-8-sig")
    chk[chk.outlier].to_csv(interim / "extract_outliers.csv", index=False, encoding="utf-8-sig")
    forb_cols = list(FORBIDDEN_ANY) + list(FORBIDDEN_PARA)
    left = chk[chk[forb_cols].sum(axis=1) > 0][["meeting_date"] + forb_cols]
    left.to_csv(interim / "extract_forbidden_left.csv", index=False, encoding="utf-8-sig")
    print(f"상관(n_chars, wcb_num_sentences) = {corr:.3f} (n={len(sub)}), 이상 문서 {int(chk.outlier.sum())}, "
          f"금지 문구 남은 문서 {len(left)}")

    # ---- 특수 사례 ----
    sp = []
    for date, why in sorted(SPECIAL_CASES.items()):
        r = results[date]
        sp.append({"meeting_date": date, "issue": why, "heading_roles": ">".join(r["roles"]),
                   "blocks": ";".join(f"{b['section']}(p{b['page_start']}-{b['page_end']},{b['extract_method']},"
                                      f"{b['n_chars']}자,end={b['end_rule']})" for b in r["blocks"]),
                   "unknown_roman": " | ".join(r["unknown_roman"]),
                   "flags": ";".join(b["flag"] for b in r["blocks"] if b["flag"])})
    pd.DataFrame(sp).to_csv(interim / "special_cases.csv", index=False, encoding="utf-8-sig")

    # ---- 검수 표본 20 (특수 사례 제외) ----
    rng = random.Random(args.seed)
    pools = {}
    for d in docs:
        if d["date"] not in SPECIAL_CASES:
            pools.setdefault(era_of(d["date"]), []).append(d["date"])
    quota = {"2010-2011": 3, "2012-2023.2": 14, "2023.4+": 3}
    sample = []
    for era, n in quota.items():
        for dt in sorted(rng.sample(sorted(pools[era]), n)):
            sample.append({"meeting_date": dt, "era": era})
    pd.DataFrame(sample).to_csv(interim / "audit_sample_20.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"meeting_date": s["meeting_date"], "era": s["era"], "start_ok": "", "end_ok": "",
                   "leftover_footnote": "", "memo": ""} for s in sample]).to_csv(
        interim / "audit_sections_20.csv", index=False, encoding="utf-8-sig")
    md = ["# 섹션 검수 자료 (가이드 C1, 20문서)", "",
          "각 문서: 시작 부분 3문단 / 끝 부분 3문단 / 제외된 섹션 제목. 전체 텍스트는 `data/interim/discussion_txt/`.", ""]
    for s in sample:
        r = results[s["meeting_date"]]
        md.append(f"## {s['meeting_date']} ({s['era']})")
        md.append("블록: " + "; ".join(f"{b['section']} p{b['page_start']}-{b['page_end']} "
                                      f"({b['n_chars']}자, 끝규칙 {b['end_rule']})" for b in r["blocks"]))
        md.append("")
        first_b, last_b = r["blocks"][0], r["blocks"][-1]
        md.append("**시작 3문단**")
        md.extend(f"> {p[:600]}" for p in first_b["paras"][:3])
        md.append("")
        md.append("**끝 3문단**")
        md.extend(f"> {p[:600]}" for p in last_b["paras"][-3:])
        md.append("")
        ex = [f"{b['role']}: {b['text']} (p{b['page']})" for b in r["boundaries"] if b["role"] in EXCLUDED_ROLES]
        md.append("**제외된 섹션 제목:** " + (" / ".join(ex) if ex else "(없음)"))
        md.append("")
    (interim / "audit_sections_20_packet.md").write_text("\n".join(md), encoding="utf-8")
    print("검수 표본 20문서:", [s["meeting_date"] for s in sample])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="data/raw/pdf")
    ap.add_argument("--interim", default="data/interim")
    ap.add_argument("--headings", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--seed", type=int, default=20261017)
    args = ap.parse_args()
    Path(args.interim).mkdir(parents=True, exist_ok=True)
    if args.headings:
        run_headings(args)
    elif args.diagnose:
        run_diagnose(args)
    else:
        run_extract(args)
