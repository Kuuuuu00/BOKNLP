"""P2: split discussion blocks into sentences and FLAG (never delete) vote and boilerplate sentences.

Rules: docs/annotation_guide.md C2 (v1.3) and C3.
uv run python scripts/10_split_sentences.py
Outputs (data/interim): sentences.csv, sentence_count_by_meeting.csv, split_diagnostics/*.csv, audit_votes_20.csv
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pysbd

INTERIM = Path("data/interim")

# ---------------------------------------------------------------- splitting
ABBREV_END = re.compile(
    r"(?:\b(?:U\.S|e\.g|i\.e|Mr|Mrs|Ms|Dr|No|vs|approx|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|cf|Inc|Co|Ltd)\.)$",
    re.I,
)
DECIMAL_JOIN = re.compile(r"\d\.$")
DECIMAL_NEXT = re.compile(r"^\d+(?:\.\d+)?\s?(?:%|percent|bp|basis|percentage)", re.I)
LOWER_START = re.compile(r"^[a-z]")  # stray period in source: lowercase start continues the previous sentence
ENUM_START = re.compile(r"^\((?:[ivx]+|[a-z]|\d{1,2})\)\s")  # "(ii) ..." inside a "(i) ... and (ii) ..." enumeration
MIN_CHARS = 25
COLON_SPLIT = re.compile(r"((?:were as follows|covered the following areas|the following areas|following)\s*:)\s+(?=[A-Z(])")


def split_paragraph(par, seg):
    par = re.sub(r"\s+", " ", par).strip()
    if not par:
        return []
    parts = [s.strip() for s in seg.segment(par) if s.strip()]
    merged = []
    for s in parts:
        if merged and (ABBREV_END.search(merged[-1]) or (DECIMAL_JOIN.search(merged[-1]) and DECIMAL_NEXT.match(s))
                       or LOWER_START.match(s) or ENUM_START.match(s)):
            merged[-1] = merged[-1] + " " + s
        else:
            merged.append(s)
    out = []
    for s in merged:  # fragments < 25 chars join the previous sentence
        if out and len(s) < MIN_CHARS:
            out[-1] = out[-1] + " " + s
        else:
            out.append(s)
    if len(out) > 1 and len(out[0]) < MIN_CHARS:
        out[1] = out[0] + " " + out[1]
        out = out[1:]
    final = []
    for s in out:  # colon split after "...were as follows:" when text continues on the same line
        m = COLON_SPLIT.search(s)
        if m and m.end() < len(s):
            final += [s[: m.end(1)].strip(), s[m.end():].strip()]
        else:
            final.append(s)
    return final


# ---------------------------------------------------------------- boilerplate (guide C3)
BOILERPLATE = [
    ("staff_briefing_intro", re.compile(r"^after (?:hearing )?(?:the )?(?:staff )?briefings?\b.*\b(?:following areas|following issues|discussed)\b", re.I)),
    ("discussion_were_as_follows", re.compile(r"^the\b.*\bdiscussions?\b.*\bbase rate\b.*\bwere as follows\s*:?$", re.I)),
    ("c_each_member_expressed", re.compile(r"^at the\b.*\bmeeting\b.*\beach member expressed\b", re.I)),
]

# ---------------------------------------------------------------- vote (guide C2 v1.3)
ACTION = re.compile(r"\b(?:rais\w*|rise|hik\w*|increas\w*|lower\w*|cut\w*|reduc\w*|keep\w*|kept|leav\w*|left|hold\w*|held|maintain\w*|freez\w*|froze|ease|easing|tighten\w*|adjust\w*|upward|downward|unchanged|on hold)\b", re.I)
BASE = re.compile(r"\bbase rate\b", re.I)
COND_B = re.compile(
    r"\b(?:(?:at|for|in) (?:this|the present|the current) meeting|this month|this time|(?:for|during) the intermeeting period"
    r"|until the next (?:\w+ ){0,4}meeting|for the ensuing month)\b",
    re.I,
)
AFTER_DISC = re.compile(r"^\(?\s*after the (?:detailed )?discussions\b[^,]{0,40}\babove\b.*\b(?:agreed|decided|resolved)\b", re.I)
NAMED_DISSENT = re.compile(r"\b(?:Mr|Dr|Ms|Mrs)\.?\s.*\b(?:dissent\w*|clear opposition|argued for)\b", re.I)
MEMBER_PROPOSED = re.compile(r"^\(?\s*(?:one|another|to begin,? one)\s+(?:other\s+)?member\s+(?:proposed|viewed it as appropriate)\b.*\bbase rate\b", re.I)
MEMBER_RATE_SHOULD = re.compile(
    r"^\(?\s*(?:one|another|to begin,? one)\s+(?:other\s+)?member\b.*\b(?:opinion|view|argued|stated)\b.*\brate\b[^.]{0,20}\bshould be\s+"
    r"(?:raised|lowered|cut|kept|held|maintained|left|reduced|increased|hiked)\b", re.I)
MAJORITY_DISSENT = re.compile(r"^(?:the majority of|all|a majority of|most|many)\s+members\b.*\bbase rate\b.*\b(?:while|meanwhile)\b.*\bargued for\b", re.I)
CONCRETE = re.compile(
    r"\bby\s+\d+(?:\.\d+)?\s?(?:of a\s+)?(?:bp|basis points?|percentage points?|%p|percent(?:age)? points?)\b"
    r"|\bto\s+\d+(?:\.\d+)?\s?%"
    r"|\bat\s+(?:its|the)\s+current(?:\s+[\w.%]+){0,3}\s+level\b"
    r"|\b(?:to|that)\s+(?:maintain|keep|hold|leave)\s+the\s+(?:current|present)\s+level\s+of\s+the\s+(?:Bank of Korea\s+)?Base Rate\b"
    r"|\b(?:unchanged|on hold)\b",
    re.I,
)
FUTURE = re.compile(
    r"\bgoing forward\b|\bin the future\b|\bnext (?:\w+ )?meetings?\b|\bif\b|\bshould\b|\badditional\b|\bfuture\b|\blooking ahead\b"
    r"|\bfurther\s+(?:\w+\s+){0,2}(?:cuts?|hikes?|increases?|reductions?|rises?|tightening|easing|adjustments?|changes?|raising|lowering|cutting|raise|lower)\b",
    re.I,
)
CUE = re.compile(r"\b(?:appropriate|desirable|preferable|advisable|warranted|better|best|opinion|view|argued|proposed|favou?r\w*|supported|agreed|decided|resolution|judged|deemed|resolved)\b|\bfound\s+(?:it\s+)?(?:appropriate|desirable)\b", re.I)


def classify(s):
    for name, rx in BOILERPLATE:
        if rx.search(s):
            return 0, "", 1, name
    if AFTER_DISC.search(s):
        return 1, "after_discussions", 0, ""
    if NAMED_DISSENT.search(s) and BASE.search(s):
        return 1, "named_dissent", 0, ""
    if MEMBER_PROPOSED.search(s):
        return 1, "member_proposed", 0, ""
    if MEMBER_RATE_SHOULD.search(s):
        return 1, "member_rate_should", 0, ""
    if MAJORITY_DISSENT.search(s):
        return 1, "majority_with_dissent", 0, ""
    a = BASE.search(s) and ACTION.search(s)
    if a and COND_B.search(s):
        return 1, "action_base_rate_this_meeting", 0, ""
    if a and CUE.search(s) and CONCRETE.search(s) and not FUTURE.search(s):
        return 1, "noB_concrete_decision", 0, ""
    return 0, "", 0, ""


def era_of(d):
    return "2010-2011" if d < "2012-01-01" else ("2012-2023.2" if d < "2023-03-01" else "2023.4+")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(INTERIM / "discussion_blocks.csv"))
    ap.add_argument("--audit-seed", type=int, default=20261017)
    args = ap.parse_args()
    blocks = pd.read_csv(args.inp).sort_values(["meeting_date", "block_id"], kind="stable")
    # keep econ before policy within a meeting
    order = {"econ": 0, "policy": 1, "discussion": 0}
    blocks = blocks.assign(_o=blocks["section"].map(order)).sort_values(["meeting_date", "_o"], kind="stable")
    seg = pysbd.Segmenter(language="en", clean=False)
    rows = []
    for d, g in blocks.groupby("meeting_date", sort=True):
        n = 0
        for _, b in g.iterrows():
            for par in re.split(r"\n\s*\n", str(b["text_raw"])):
                for s in split_paragraph(par, seg):
                    n += 1
                    iv, vr, ib, br = classify(s)
                    rows.append({"meeting_date": d, "sent_id": n, "block_id": b["block_id"], "section": b["section"],
                                 "sent_raw": s, "sent_norm": re.sub(r"\s+", " ", s.lower()).strip(),
                                 "is_vote": iv, "vote_rule": vr, "is_boilerplate": ib, "boilerplate_rule": br,
                                 "n_chars": len(s)})
    sent = pd.DataFrame(rows)
    sent.to_csv(INTERIM / "sentences.csv", index=False, encoding="utf-8-sig")
    diagnostics(sent, args)


def diagnostics(sent, args):
    dd = INTERIM / "split_diagnostics"
    dd.mkdir(exist_ok=True)
    sent["era"] = sent["meeting_date"].map(era_of)
    sent["year"] = sent["meeting_date"].str[:4]
    cnt = sent.groupby("meeting_date").agg(era=("era", "first"), n_all=("sent_id", "size"), n_vote=("is_vote", "sum"),
                                           n_boilerplate=("is_boilerplate", "sum")).reset_index()
    cnt["n_usable"] = cnt["n_all"] - cnt["n_vote"] - cnt["n_boilerplate"]
    cnt.to_csv(INTERIM / "sentence_count_by_meeting.csv", index=False)
    cnt.groupby("era")["n_all"].describe().to_csv(dd / "n_all_by_era.csv")
    cnt.groupby("era")["n_usable"].describe().to_csv(dd / "n_usable_by_era.csv")
    cnt[cnt["n_usable"] < 10].to_csv(dd / "n_usable_lt10.csv", index=False)
    yr = sent.groupby("year").agg(n=("sent_id", "size"), vote_rate=("is_vote", "mean"), boilerplate_rate=("is_boilerplate", "mean"))
    yr.to_csv(dd / "rates_by_year.csv")
    sent[sent["n_chars"] < 25].to_csv(dd / "short_lt25.csv", index=False, encoding="utf-8-sig")
    sent[sent["n_chars"] > 1000].to_csv(dd / "long_gt1000.csv", index=False, encoding="utf-8-sig")
    noend = sent[~sent["sent_raw"].str.rstrip(" )\"'’”").str.endswith((".", "?", "!", ":"))]
    noend.to_csv(dd / "no_terminal_period.csv", index=False, encoding="utf-8-sig")
    sent.groupby(["vote_rule"]).size().to_csv(dd / "vote_rule_counts.csv")
    mm = pd.read_csv("data/metadata/meeting_master.csv", encoding="utf-8-sig")[["meeting_date", "wcb_num_sentences"]].dropna()
    j = cnt.merge(mm, on="meeting_date")
    corr = float(np.corrcoef(j["n_all"], j["wcb_num_sentences"])[0, 1])
    # audit_votes_20
    a20 = pd.read_csv(INTERIM / "audit_sample_20.csv", encoding="utf-8-sig")["meeting_date"].tolist()
    s20 = sent[sent["meeting_date"].isin(a20)]
    parts = []
    for typ, m in [("flagged_vote", s20["is_vote"] == 1),
                   ("candidate_miss", (s20["is_vote"] == 0) & s20["sent_raw"].str.contains("Base Rate", case=False, regex=False)),
                   ("boilerplate", s20["is_boilerplate"] == 1)]:
        x = s20[m].copy()
        x["type"] = typ
        parts.append(x)
    av = pd.concat(parts)[["meeting_date", "sent_id", "type", "sent_raw", "is_vote", "vote_rule"]]
    av["reviewer_judgment"] = ""
    av["memo"] = ""
    av.to_csv(INTERIM / "audit_votes_20.csv", index=False, encoding="utf-8-sig")
    print("meetings", len(cnt), "sentences", len(sent), "corr(n_all, wcb_num_sentences) =", round(corr, 3), "n=", len(j))
    print(cnt.groupby("era")[["n_all", "n_vote", "n_boilerplate", "n_usable"]].median())
    print("n_usable<10:", int((cnt["n_usable"] < 10).sum()), "min usable", int(cnt["n_usable"].min()))
    print("short<25:", int((sent["n_chars"] < 25).sum()), "long>1000:", int((sent["n_chars"] > 1000).sum()), "no terminal:", len(noend))
    print(yr.round(3).to_string())
    print(sent["vote_rule"].value_counts().to_string())
    print(av["type"].value_counts().to_string())


if __name__ == "__main__":
    main()
