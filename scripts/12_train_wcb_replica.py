"""Reproduce-train the WCB general stance model (paper App. C.3, C.7.1 Table 19).

Data: data/raw/wcb_hf/<seed>/{train,val}.parquet  (the test split is never read here).
Spec: roberta-large, lowercased input, labels 0 neutral / 1 hawkish / 2 dovish / 3 irrelevant,
AdamW, cross-entropy, lr 1e-6, effective batch 32, bf16, <=50 epochs,
early stopping on validation weighted F1, seed 944601 (torch/numpy/random/shuffle).
Not in paper (user-fixed defaults): max_length = 99.5% quantile of train token lengths (cap 512),
weight decay 0.01, constant LR (no warmup), patience 5.

uv run python scripts/12_train_wcb_replica.py                  # full training
uv run python scripts/12_train_wcb_replica.py --max-steps 200  # timing run (writes to a temp dir)
"""
import argparse
import hashlib
import json
import math
import random
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LABEL2ID = {"neutral": 0, "hawkish": 1, "dovish": 2, "irrelevant": 3}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def pkg_version(name):
    try:
        return version(name)
    except Exception:
        return "not installed"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_split(seed, split):
    df = pd.read_parquet(f"data/raw/wcb_hf/{seed}/{split}.parquet")
    assert df["sentences"].notna().all(), "null sentence"
    texts = df["sentences"].astype(str).str.lower().tolist()  # card: do_lower_case
    labels = df["stance_label"].map(LABEL2ID)
    assert labels.notna().all(), "unknown label"
    return texts, labels.astype(int).to_numpy()


def encode(tok, texts, max_len):
    return tok(texts, truncation=True, max_length=max_len)["input_ids"]


def collate(ids, labels, idx, pad_id, device):
    seqs = [ids[i] for i in idx]
    m = max(len(s) for s in seqs)
    x = torch.full((len(seqs), m), pad_id, dtype=torch.long)
    a = torch.zeros((len(seqs), m), dtype=torch.long)
    for r, s in enumerate(seqs):
        x[r, : len(s)] = torch.tensor(s)
        a[r, : len(s)] = 1
    y = torch.tensor(labels[idx], dtype=torch.long)
    return x.to(device), a.to(device), y.to(device)


@torch.no_grad()
def evaluate(model, ids, labels, pad_id, device, bs=64):
    model.eval()
    order = np.argsort([len(s) for s in ids])
    preds = np.zeros(len(ids), dtype=int)
    tot_loss = 0.0
    for i in range(0, len(order), bs):
        idx = order[i : i + bs]
        x, a, y = collate(ids, labels, idx, pad_id, device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(input_ids=x, attention_mask=a).logits
        tot_loss += torch.nn.functional.cross_entropy(logits.float(), y, reduction="sum").item()
        preds[idx] = logits.argmax(-1).cpu().numpy()
    model.train()
    return (
        tot_loss / len(ids),
        f1_score(labels, preds, average="weighted"),
        f1_score(labels, preds, average="macro"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=944601)
    ap.add_argument("--base-model", default="roberta-large")
    ap.add_argument("--lr", type=float, default=1e-6)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--eff-batch", type=int, default=32)
    ap.add_argument("--micro-batch", type=int, default=16)
    ap.add_argument("--max-epochs", type=int, default=50)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--max-length-quantile", type=float, default=0.995)
    ap.add_argument("--max-length-cap", type=int, default=512)
    ap.add_argument("--max-steps", type=int, default=0, help="timing run: stop after N optimizer steps, no checkpoint")
    ap.add_argument("--out", default="models/wcb_stance_replica")
    args = ap.parse_args()
    assert args.eff_batch % args.micro_batch == 0
    timing = args.max_steps > 0
    out = Path(args.out if not timing else "models/_timing_tmp")
    if (out / "best").exists():
        raise SystemExit(f"{out/'best'} exists: refusing to overwrite (move it first)")
    out.mkdir(parents=True, exist_ok=True)

    set_seed(args.seed)
    torch.backends.cudnn.deterministic = True
    device = "cuda"
    tok = AutoTokenizer.from_pretrained(args.base_model)
    tr_x, tr_y = load_split(args.seed, "train")
    va_x, va_y = load_split(args.seed, "val")

    raw_len = np.array([len(s) for s in tok(tr_x)["input_ids"]])
    max_len = int(min(args.max_length_cap, math.ceil(np.quantile(raw_len, args.max_length_quantile))))
    print(f"train token len: max {raw_len.max()}, q{args.max_length_quantile} -> max_length {max_len}")
    tr_ids, va_ids = encode(tok, tr_x, max_len), encode(tok, va_x, max_len)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model, num_labels=4, id2label=ID2LABEL, label2id=LABEL2ID
    ).to(device)
    model.train()
    no_decay = ["bias", "LayerNorm.weight"]
    groups = [
        {"params": [p for n, p in model.named_parameters() if not any(k in n for k in no_decay)],
         "weight_decay": args.weight_decay},
        {"params": [p for n, p in model.named_parameters() if any(k in n for k in no_decay)],
         "weight_decay": 0.0},
    ]
    opt = torch.optim.AdamW(groups, lr=args.lr)  # constant LR, no warmup

    cfg = {
        **vars(args),
        "max_length": max_len,
        "label2id": LABEL2ID,
        "precision": "bf16 autocast (fp32 master weights)",
        "lowercase_input": True,
        "lr_schedule": "constant, no warmup",
        "accumulation_steps": args.eff_batch // args.micro_batch,
        "n_train": len(tr_x),
        "n_val": len(va_x),
        "train_sha256": sha256(f"data/raw/wcb_hf/{args.seed}/train.parquet"),
        "val_sha256": sha256(f"data/raw/wcb_hf/{args.seed}/val.parquet"),
        "packages": {p: pkg_version(p) for p in ["torch", "transformers", "tokenizers", "safetensors", "numpy", "pandas", "scikit-learn", "pyarrow"]},
        "cuda": torch.version.cuda,
        "selection_metric": "val_weighted_f1 (strict >)",
        "inference_note": "inputs MUST be lowercased before tokenization (tokenizer itself is cased)",
        "grad_clipping": "none (not in spec)",
        "determinism": "seeded; cudnn.deterministic; bf16 autocast is not bit-exact",
        "gpu": torch.cuda.get_device_name(0),
        "test_split_used_in_training": False,
    }
    (out / "train_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    gen = torch.Generator().manual_seed(args.seed)  # data shuffle
    n = len(tr_ids)
    best_f1, best_epoch, bad, step, log = -1.0, 0, 0, 0, []
    t0 = time.time()
    for epoch in range(1, args.max_epochs + 1):
        perm = torch.randperm(n, generator=gen).numpy()
        run_loss, seen = 0.0, 0
        for s in range(0, n, args.eff_batch):
            chunk = perm[s : s + args.eff_batch]
            for m in range(0, len(chunk), args.micro_batch):
                idx = chunk[m : m + args.micro_batch]
                x, a, y = collate(tr_ids, tr_y, idx, tok.pad_token_id, device)
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    logits = model(input_ids=x, attention_mask=a).logits
                loss = torch.nn.functional.cross_entropy(logits.float(), y, reduction="sum") / len(chunk)
                loss.backward()
                run_loss += loss.item() * len(chunk)
                seen += len(idx)
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if timing and step >= args.max_steps:
                el = time.time() - t0
                steps_per_epoch = math.ceil(n / args.eff_batch)
                est_epoch = el / step * steps_per_epoch
                print(json.dumps({
                    "steps": step, "seconds": round(el, 1), "sec_per_step": round(el / step, 3),
                    "steps_per_epoch": steps_per_epoch, "est_epoch_sec": round(est_epoch, 1),
                    "est_epoch_with_val_sec": round(est_epoch * 1.07, 1),
                    "est_50_epoch_hours": round(est_epoch * 1.07 * 50 / 3600, 2),
                    "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
                    "train_loss_so_far": round(run_loss / seen, 4),
                }, indent=2))
                return
        v_loss, v_wf1, v_mf1 = evaluate(model, va_ids, va_y, tok.pad_token_id, device)
        row = {"epoch": epoch, "step": step, "train_loss": run_loss / seen, "val_loss": v_loss,
               "val_weighted_f1": v_wf1, "val_macro_f1": v_mf1, "elapsed_sec": round(time.time() - t0, 1)}
        log.append(row)
        pd.DataFrame(log).to_csv(out / "train_log.csv", index=False)
        print(row, flush=True)
        if v_wf1 > best_f1:
            best_f1, best_epoch, bad = v_wf1, epoch, 0
            model.save_pretrained(out / "best")
            tok.save_pretrained(out / "best")
            cfg.update({"best_epoch": best_epoch, "best_val_weighted_f1": best_f1, "epochs_run": len(log)})
            (out / "train_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            bad += 1
            if bad >= args.patience:
                print(f"early stop at epoch {epoch}; best epoch {best_epoch}")
                break
    cfg.update({"best_epoch": best_epoch, "best_val_weighted_f1": best_f1,
                "epochs_run": len(log), "train_seconds": round(time.time() - t0, 1)})
    (out / "train_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
