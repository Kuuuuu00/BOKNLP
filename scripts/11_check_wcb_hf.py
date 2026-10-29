"""Integrity checks for data/raw/wcb_hf (read-only). Writes data/interim/wcb_hf_checks.txt.

uv run python scripts/11_check_wcb_hf.py
"""
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/wcb_hf")
FINAL = Path("data/raw/wcb/final_data.csv")
OUT = Path("data/interim/wcb_hf_checks.txt")
SEEDS = ["5768", "78516", "944601"]
lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def norm(s):
    s = str(s).lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


d = {s: {k: pd.read_parquet(RAW / s / f"{k}.parquet") for k in ("train", "val", "test")} for s in SEEDS}
for s in SEEDS:
    log(s, {k: len(v) for k, v in d[s].items()})
tr = d["944601"]["train"]
log("label dist (944601) per split:")
for k, v in d["944601"].items():
    log(" ", k, v["stance_label"].value_counts().to_dict())
log("bank_name rows per split (944601):")
log(pd.DataFrame({k: v["bank_name"].value_counts() for k, v in d["944601"].items()}).fillna(0).astype(int).to_string())
# lowercase check
allt = pd.concat(d["944601"].values())
lower_ratio = (allt["sentences"] == allt["sentences"].str.lower()).mean()
log("already lowercase ratio:", round(lower_ratio, 6))
# leakage (normalized) across splits, per seed
for s in SEEDS:
    sets = {k: set(v["sentences"].map(norm)) for k, v in d[s].items()}
    log(s, "overlap train&val", len(sets["train"] & sets["val"]), "train&test", len(sets["train"] & sets["test"]),
        "val&test", len(sets["val"] & sets["test"]))
    dup = {k: int(v["sentences"].map(norm).duplicated().sum()) for k, v in d[s].items()}
    log(s, "within-split duplicates", dup)
# BOK reconciliation
fin = pd.read_csv(FINAL)
fin["n"] = fin["sentences"].map(norm)
log("final_data rows", len(fin), "unique norm", fin["n"].nunique(), "label dist", fin["stance_label"].value_counts().to_dict())
bok = {k: v[v["bank_name"] == "bank_of_korea"] for k, v in d["944601"].items()}
log("BOK rows in 944601:", {k: len(v) for k, v in bok.items()})
fl = fin.groupby("n")["stance_label"].agg(lambda x: set(x))
rows = []
for k, v in bok.items():
    n = v["sentences"].map(norm)
    inf = n.isin(fl.index)
    lab_ok = [lab in fl[x] for x, lab in zip(n[inf], v["stance_label"][inf])]
    rows.append((k, len(v), int(inf.sum()), int(sum(lab_ok))))
    log(f"  {k}: rows {len(v)}, sentence found in final_data {int(inf.sum())}, label equal {int(sum(lab_ok))}")
hf_all = set(pd.concat(bok.values())["sentences"].map(norm))
log("final_data sentences not found in HF BOK rows:", len(set(fin["n"]) - hf_all))
log("HF BOK sentences not in final_data:", len(hf_all - set(fin["n"])))
OUT.write_text("\n".join(lines), encoding="utf-8")
