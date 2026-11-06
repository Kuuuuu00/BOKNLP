"""P2: simulate guide v1.4 CANDIDATE vote rules on all sentences WITHOUT applying them (nothing in data/interim/sentences.csv changes).
uv run python scripts/10e_simulate_v14.py [--seed 20261106 --n-sample 20]
Candidates (flags on top of the v1.3 classify() in 10_split_sentences.py):
  F  FUTURE words that appear only AFTER the concrete decision phrase no longer block the no-B rule (guide C2 v1.2 item 4 currently scans the whole sentence)
  S  subject variants 'the (same) member / this member / he / she' accepted in MEMBER_PROPOSED / MEMBER_RATE_SHOULD (+ 'adjusted')
  N  decision cues 'called for / commented / noted / saw / stated / said' and condition B 'at this point in time'
Sanity: with no flag the result must equal the stored is_vote exactly.
Outputs (data/interim/sim_v14/): sim_changes.csv (every changed sentence), sim_summary.csv, judge_packet.csv (blind sample for the subagent), judge_key.csv.
"""
import argparse
import importlib.util
import re
from pathlib import Path

import pandas as pd

INTERIM = Path("data/interim")
OUT = INTERIM / "sim_v14"
spec = importlib.util.spec_from_file_location("sp", "scripts/10_split_sentences.py")
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)

SUBJ = r"(?:the(?:\s+same|\s+other)?\s+member|this\s+member|he|she)"
S_PROPOSED = re.compile(r"^\(?\s*(?:then,?\s+|also,?\s+)?" + SUBJ + r"\s+(?:then\s+|also\s+)?(?:proposed|viewed it as appropriate)\b.*\bbase rate\b", re.I)
S_RATE_SHOULD = re.compile(
    r"^\(?\s*(?:in addition,?\s+|moreover,?\s+)?" + SUBJ + r"\b.*\b(?:opinion|view|argued|stated)\b.*\brate\b[^.]{0,20}\bshould be\s+"
    r"(?:raised|lowered|cut|kept|held|maintained|left|reduced|increased|hiked|adjusted)\b", re.I)
N_CUE = re.compile(r"\b(?:called for|commented|noted|saw|stated|said)\b", re.I)
N_COND_B = re.compile(r"\bat this point in time\b", re.I)


def classify_v14(s, flags=()):
    for name, rx in sp.BOILERPLATE:
        if rx.search(s):
            return 0, ""
    if sp.AFTER_DISC.search(s):
        return 1, "after_discussions"
    if sp.NAMED_DISSENT.search(s) and sp.BASE.search(s):
        return 1, "named_dissent"
    if sp.MEMBER_PROPOSED.search(s) or ("S" in flags and S_PROPOSED.search(s)):
        return 1, "member_proposed"
    if sp.MEMBER_RATE_SHOULD.search(s) or ("S" in flags and S_RATE_SHOULD.search(s)):
        return 1, "member_rate_should"
    if sp.MAJORITY_DISSENT.search(s):
        return 1, "majority_with_dissent"
    a = sp.BASE.search(s) and sp.ACTION.search(s)
    if a and (sp.COND_B.search(s) or ("N" in flags and N_COND_B.search(s))):
        return 1, "action_base_rate_this_meeting"
    cue = sp.CUE.search(s) or ("N" in flags and N_CUE.search(s))
    c = sp.CONCRETE.search(s)
    if a and cue and c:
        fut = sp.FUTURE.search(s[: c.end()]) if "F" in flags else sp.FUTURE.search(s)
        if not fut:
            return 1, "noB_concrete_decision"
    return 0, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sentences", default=str(INTERIM / "sentences.csv"))
    ap.add_argument("--judged", default=str(INTERIM / "audit_votes_20_judged.csv"))
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--n-sample", type=int, default=20)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    s = pd.read_csv(args.sentences, encoding="utf-8-sig", dtype={"meeting_date": str})
    j = pd.read_csv(args.judged, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    s["era"] = s["meeting_date"].map(sp.era_of)
    docs20 = set(j["meeting_date"])
    base = [classify_v14(x)[0] for x in s["sent_raw"]]
    assert (pd.Series(base) == s["is_vote"]).all(), "v1.3 reproduction failed"
    s["bp"] = s["is_boilerplate"]
    print("sanity ok: no-flag reproduction equals stored is_vote for", len(s), "sentences")

    combos = {"F": ("F",), "S": ("S",), "N": ("N",), "F+S+N": ("F", "S", "N")}
    summ, changes = [], []
    for name, fl in combos.items():
        new = pd.Series([classify_v14(x, fl)[0] for x in s["sent_raw"]])
        rule = pd.Series([classify_v14(x, fl)[1] for x in s["sent_raw"]])
        up, down = (s["is_vote"] == 0) & (new == 1), (s["is_vote"] == 1) & (new == 0)
        ch = s[up | down].copy()
        ch["candidate"], ch["new_is_vote"], ch["new_rule"] = name, new[up | down].values, rule[up | down].values
        ch["in_audit20"] = ch["meeting_date"].isin(docs20)
        changes.append(ch)
        # in-sample effect on the 20 reviewed documents (tuning set; NOT a validation)
        k = j.merge(s[["meeting_date", "sent_id"]].assign(new=new.values), on=["meeting_date", "sent_id"])
        cm = k[k["type"] == "candidate_miss"]
        summ.append({"candidate": name, "0to1": int(up.sum()), "1to0": int(down.sum()),
                     **{f"0to1_{e}": int((up & (s['era'] == e)).sum()) for e in sp_eras()},
                     "0to1_in_audit20": int((up & s["meeting_date"].isin(docs20)).sum()),
                     "0to1_outside_audit20": int((up & ~s["meeting_date"].isin(docs20)).sum()),
                     "audit20_missed_caught": int(((cm["reviewer_judgment"] == "missed") & (cm["new"] == 1)).sum()),
                     "audit20_ok_flipped_to_vote": int(((cm["reviewer_judgment"] == "ok") & (cm["new"] == 1)).sum()),
                     "boilerplate_rows_touched": int((up & (s["bp"] == 1)).sum())})
    summ = pd.DataFrame(summ)
    allch = pd.concat(changes)
    allch.to_csv(OUT / "sim_changes.csv", index=False, encoding="utf-8-sig")
    summ.to_csv(OUT / "sim_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summ.T.to_string())

    # blind sample for the rule-blind subagent: per candidate (single-flag), up to n 0->1 sentences outside the 20 audit docs, era-stratified
    rng = pd.Series(range(len(s)))
    pk, key = [], []
    for name in ("F", "S", "N"):
        c = allch[(allch["candidate"] == name) & (allch["new_is_vote"] == 1) & (~allch["in_audit20"])]
        if len(c) <= args.n_sample:
            pick = c
        else:
            share = (c["era"].value_counts(normalize=True) * args.n_sample).round().astype(int).clip(lower=1)
            pick = pd.concat([c[c["era"] == e].sample(min(n, (c["era"] == e).sum()), random_state=args.seed) for e, n in share.items()])
            pick = pick.sample(min(len(pick), args.n_sample), random_state=args.seed) if len(pick) > args.n_sample else pick
        print(f"candidate {name}: pool outside audit20 = {len(c)}, sampled {len(pick)}, eras {pick['era'].value_counts().to_dict()}")
        key.append(pick[["candidate", "meeting_date", "sent_id", "era", "new_rule"]])
    key = pd.concat(key)
    # a sentence changed by several candidates is judged once
    key = key.sort_values("candidate").drop_duplicates(["meeting_date", "sent_id"], keep="first").sample(frac=1, random_state=args.seed).reset_index(drop=True)
    key["item"] = range(1, len(key) + 1)
    full = s.set_index(["meeting_date", "sent_id"])["sent_raw"]
    key["sent_raw"] = [full[(d, i)] for d, i in zip(key.meeting_date, key.sent_id)]
    key["prev"] = [full.get((d, i - 1), "") for d, i in zip(key.meeting_date, key.sent_id)]
    key["next"] = [full.get((d, i + 1), "") for d, i in zip(key.meeting_date, key.sent_id)]
    key.to_csv(OUT / "judge_key.csv", index=False, encoding="utf-8-sig")
    key[["item", "prev", "sent_raw", "next"]].to_csv(OUT / "judge_packet.csv", index=False, encoding="utf-8-sig")
    print("judge packet items:", len(key))


def sp_eras():
    return ["2010-2011", "2012-2023.2", "2023.4+"]


if __name__ == "__main__":
    main()
