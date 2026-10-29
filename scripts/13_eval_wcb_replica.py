"""Final one-shot test evaluation of the replica WCB stance model.

Reads the seed-944601 TEST split once. Computes weighted/macro F1 (all rows and bank_of_korea rows),
bootstrap 95% CI (fixed seed), BOK confusion matrix, and compares with the paper (Table 1, RoBERTa-Large BoK 0.755 +/- 0.019).
No reproduction pass/fail threshold is applied (decision Q2: report only).
Refuses to run again if the output exists (test is evaluated once); pass --allow-rerun only with an explicit decision.

uv run python scripts/13_eval_wcb_replica.py
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LABEL2ID = {"neutral": 0, "hawkish": 1, "dovish": 2, "irrelevant": 3}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
PAPER_BOK, PAPER_BOK_PM = 0.755, 0.019
OUT_F1 = Path("data/processed/table1_repro_f1.csv")
OUT_CM = Path("data/interim/replica_confusion_bok.csv")


@torch.no_grad()
def predict(model, tok, texts, max_len, bs=64):
    order = np.argsort([len(t) for t in texts])
    preds = np.zeros(len(texts), dtype=int)
    for i in range(0, len(order), bs):
        idx = order[i : i + bs]
        enc = tok([texts[j] for j in idx], truncation=True, max_length=max_len, padding=True, return_tensors="pt").to("cuda")
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(**enc).logits
        preds[idx] = logits.argmax(-1).cpu().numpy()
    return preds


def boot_ci(y, p, avg, n_boot, rng):
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        vals.append(f1_score(y[i], p[i], average=avg, labels=[0, 1, 2, 3], zero_division=0))
    return np.percentile(vals, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="models/wcb_stance_replica")
    ap.add_argument("--split-seed", default="944601")
    ap.add_argument("--boot-seed", type=int, default=944601)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--allow-rerun", action="store_true")
    args = ap.parse_args()
    if OUT_F1.exists() and not args.allow_rerun:
        raise SystemExit(f"{OUT_F1} exists: the test set is evaluated once. Not re-running.")
    cfg = json.loads((Path(args.model_dir) / "train_config.json").read_text(encoding="utf-8"))
    assert cfg["seed"] == int(args.split_seed), "model was trained on a different split seed"
    max_len = cfg["max_length"]
    tok = AutoTokenizer.from_pretrained(Path(args.model_dir) / "best")
    model = AutoModelForSequenceClassification.from_pretrained(Path(args.model_dir) / "best").to("cuda").eval()
    assert model.config.label2id == LABEL2ID

    df = pd.read_parquet(f"data/raw/wcb_hf/{args.split_seed}/test.parquet")  # the only read of the test split
    y = df["stance_label"].map(LABEL2ID).to_numpy()
    p = predict(model, tok, df["sentences"].astype(str).str.lower().tolist(), max_len)

    rng = np.random.default_rng(args.boot_seed)
    rows, cm_rows = [], []
    for name, mask in [("all", np.ones(len(df), bool)), ("bank_of_korea", (df["bank_name"] == "bank_of_korea").to_numpy())]:
        yy, pp = y[mask], p[mask]
        for metric, avg in [("weighted_f1", "weighted"), ("macro_f1", "macro")]:
            val = f1_score(yy, pp, average=avg, labels=[0, 1, 2, 3], zero_division=0)
            lo, hi = boot_ci(yy, pp, avg, args.n_boot, rng)
            paper = PAPER_BOK if (name == "bank_of_korea" and metric == "weighted_f1") else np.nan
            rows.append({"subset": name, "n": int(mask.sum()), "metric": metric, "value": val, "ci_low": lo,
                         "ci_high": hi, "paper_value": paper,
                         "diff_vs_paper": val - paper if paper == paper else np.nan,
                         "paper_pm": PAPER_BOK_PM if paper == paper else np.nan})
        if name == "bank_of_korea":
            cm = confusion_matrix(yy, pp, labels=[0, 1, 2, 3])
            cm_rows = pd.DataFrame(cm, index=[f"true_{ID2LABEL[i]}" for i in range(4)],
                                   columns=[f"pred_{ID2LABEL[i]}" for i in range(4)])
    OUT_F1.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_F1, index=False)
    cm_rows.to_csv(OUT_CM)
    print(pd.DataFrame(rows).to_string())
    print(cm_rows.to_string())


if __name__ == "__main__":
    main()
