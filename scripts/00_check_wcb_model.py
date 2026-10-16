"""WCB stance 모델 다운로드 확인 + 동작 점검 스크립트.

사전 준비 (터미널):
    pip install -U transformers torch "huggingface_hub[cli]" pandas scikit-learn
    hf auth login            # read 토큰 입력
    hf download gtfintechlab/model_WCB_stance_label --local-dir models/wcb_stance

실행:
    python check_wcb_model.py --csv data/final_data/bank_of_korea/final_data.csv
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", default="models/wcb_stance")
parser.add_argument("--csv", default="data/raw/wcb/final_data.csv")
parser.add_argument("--n", type=int, default=200, help="점검에 쓸 문장 수")
args = parser.parse_args()

# 1) config 확인: 모델 크기와 라벨 매핑 (계획서 부록 A 항목)
cfg = AutoConfig.from_pretrained(args.model_dir)
print("model_type        :", cfg.model_type)
print("hidden_size       :", cfg.hidden_size, "(1024면 large, 768이면 base)")
print("num_hidden_layers :", cfg.num_hidden_layers, "(24면 large, 12면 base)")
print("id2label          :", cfg.id2label)
print("max_position      :", cfg.max_position_embeddings)

print("local files       :", sorted(p.name for p in Path(args.model_dir).iterdir()))

# 2) 모델 로드
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained(args.model_dir)
model = AutoModelForSequenceClassification.from_pretrained(args.model_dir).to(device).eval()

# 모델 카드 라벨 정의 (config의 id2label이 LABEL_0..3로만 되어 있을 때 사용)
CARD_MAP = {0: "neutral", 1: "hawkish", 2: "dovish", 3: "irrelevant"}


def predict(sentences, batch_size=32):
    out = []
    for i in range(0, len(sentences), batch_size):
        # WCB는 소문자 입력으로 학습됨. RoBERTa 토크나이저는 do_lower_case를 무시할 수 있으므로 직접 소문자화
        batch = [s.lower() for s in sentences[i:i + batch_size]]
        enc = tok(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        out.extend(logits.argmax(-1).tolist())
    return out


# 3) 소문자화가 결과를 바꾸는지 확인 (같은 문장, 대소문자만 다름)
s = "Most members agreed that inflationary pressures would build up going forward."
enc_raw = tok(s)["input_ids"]
enc_low = tok(s.lower())["input_ids"]
print("\n토크나이저가 자동 소문자화하는가:", enc_raw == enc_low)

# 4) final_data.csv로 동작 점검
#    주의: 이 1,000문장 중 700개는 모델 학습에 쓰였으므로 이 수치는 성능이 아니라 '라벨 매핑이 맞는지' 확인용
df = pd.read_csv(args.csv).sample(n=min(args.n, 1000), random_state=0)
pred_ids = predict(df["sentences"].tolist())
df["pred"] = [CARD_MAP[i] for i in pred_ids]
acc = (df["pred"] == df["stance_label"]).mean()
print(f"\n점검 정확도 (학습 데이터 포함, 매핑 확인용): {acc:.3f}  ← 0.25 근처면 매핑이 틀린 것")
print(pd.crosstab(df["stance_label"], df["pred"], rownames=["gold"], colnames=["pred"]))

json.dump({"id2label": cfg.id2label, "hidden_size": cfg.hidden_size,
           "layers": cfg.num_hidden_layers, "sanity_acc": round(float(acc), 4)},
          open("wcb_model_check.json", "w"), ensure_ascii=False, indent=2)
print("\n저장: wcb_model_check.json")
