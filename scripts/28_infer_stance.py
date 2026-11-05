"""P4-c: sentence-level stance inference with the replica WCB model (plan number 14_infer_stance.py -> actual file 28_).
Same preprocessing as 12_train / 13_eval: lowercase, roberta-large tokenizer (cased vocab), truncation to max_length,
dynamic padding, length-sorted batches of 64, bf16 autocast, argmax over 4 classes.
Reads only the model dir, sentences.csv (or the seed-944601 VAL split for --mode val). Never reads the test split, indices or rate data.

uv run python scripts/28_infer_stance.py --mode val                      # pipeline check against train_log.csv
uv run python scripts/28_infer_stance.py --mode corpus --max-length 103  # all sentences -> sentence_stance.csv
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LABEL2ID = {"neutral": 0, "hawkish": 1, "dovish": 2, "irrelevant": 3}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


@torch.no_grad()
def predict_proba(model, tok, texts, max_len, bs=64):
    texts = [str(t).lower() for t in texts]
    order = np.argsort([len(t) for t in texts], kind="stable")
    probs = np.zeros((len(texts), 4), dtype=np.float32)
    for i in range(0, len(order), bs):
        idx = order[i : i + bs]
        enc = tok([texts[j] for j in idx], truncation=True, max_length=max_len, padding=True, return_tensors="pt").to("cuda")
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(**enc).logits
        probs[idx] = torch.softmax(logits.float(), dim=-1).cpu().numpy()
    return probs


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["val", "corpus"], required=True)
    ap.add_argument("--model-dir", default="models/wcb_stance_replica")
    ap.add_argument("--max-length", type=int, default=None, help="default: train_config max_length")
    ap.add_argument("--in", dest="inp", default="data/interim/sentences.csv")
    ap.add_argument("--out", default="data/interim/sentence_stance.csv")
    ap.add_argument("--split-seed", default="944601")
    ap.add_argument("--tol", type=float, default=0.001)
    args = ap.parse_args()
    md = Path(args.model_dir)
    cfg = json.loads((md / "train_config.json").read_text(encoding="utf-8"))
    max_len = args.max_length or cfg["max_length"]
    torch.backends.cudnn.deterministic = True
    tok = AutoTokenizer.from_pretrained(md / "best")
    model = AutoModelForSequenceClassification.from_pretrained(md / "best").to("cuda").eval()
    assert model.config.label2id == LABEL2ID
    assert args.mode == "corpus" or cfg["seed"] == int(args.split_seed), "split seed differs from the training seed"
    if args.mode == "val":
        val = pd.read_parquet(f"data/raw/wcb_hf/{args.split_seed}/val.parquet")
        y = val["stance_label"].map(LABEL2ID).to_numpy()
        p = predict_proba(model, tok, val["sentences"].tolist(), max_len)
        f1 = f1_score(y, p.argmax(1), average="weighted", labels=[0, 1, 2, 3], zero_division=0)
        log = pd.read_csv(md / "train_log.csv")
        ref = float(log.loc[log["epoch"] == cfg["best_epoch"], "val_weighted_f1"].iloc[0])
        print(f"val n={len(val)} max_length={max_len} weighted_f1={f1:.6f} train_log(best epoch {cfg['best_epoch']})={ref:.6f} diff={f1 - ref:+.6f}")
        raise SystemExit(0 if abs(f1 - ref) <= args.tol else 1)
    s = pd.read_csv(args.inp, encoding="utf-8-sig", keep_default_na=False, dtype={"meeting_date": str})
    p = predict_proba(model, tok, s["sent_raw"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip().tolist(), max_len)
    # sent_norm is the classifier input per plan; verify it is identical to the expression above
    assert (s["sent_raw"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip() == s["sent_norm"]).all()
    out = s[["meeting_date", "sent_id"]].copy()
    out["pred_label"] = [ID2LABEL[i] for i in p.argmax(1)]
    out["p_hawkish"], out["p_dovish"], out["p_neutral"], out["p_irrelevant"] = p[:, 1], p[:, 2], p[:, 0], p[:, 3]
    out["model_revision"] = sha256(md / "best" / "model.safetensors")
    out["max_length"] = max_len
    out.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(args.out, len(out), "max_length", max_len)
    print(out["pred_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
