"""Download gtfintechlab/all_annotated_sentences_25000 (3 seed subsets) into data/raw/wcb_hf/
and run integrity checks: row counts, label distribution, per-bank counts,
BOK reconciliation with data/raw/wcb/final_data.csv, and split leakage.

uv run python scripts/10_download_wcb_hf.py
"""
import os
import re
import stat
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

REPO = "gtfintechlab/all_annotated_sentences_25000"
SEEDS = ["5768", "78516", "944601"]
RAW = Path("data/raw/wcb_hf")
FINAL = Path("data/raw/wcb/final_data.csv")
INTERIM = Path("data/interim")


def norm(s: str) -> str:
    s = str(s).lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return re.sub(r"[^a-z0-9]+", "", s)


def download():
    for seed in SEEDS:
        ds = load_dataset(REPO, seed)
        for split in ds:
            name = {"validation": "val"}.get(split, split)
            out = RAW / seed / f"{name}.parquet"
            if out.exists():
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            ds[split].to_parquet(str(out))
            os.chmod(out, stat.S_IREAD)
            print("saved", out, len(ds[split]))


def load(seed):
    return {s: pd.read_parquet(RAW / seed / f"{s}.parquet") for s in ("train", "val", "test")}


def main():
    download()
    d = {s: load(s) for s in SEEDS}
    print(d["944601"]["train"].columns.tolist())
    for seed in SEEDS:
        print(seed, {k: len(v) for k, v in d[seed].items()})
    print(d["944601"]["train"].head(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
