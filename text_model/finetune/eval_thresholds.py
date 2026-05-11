"""
Sweep decision thresholds on the val set to find the best macro-F1.

"""
import json
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.amp import autocast
from transformers import RobertaTokenizerFast, RobertaForSequenceClassification
from sklearn.metrics import f1_score

from train import GoEmotionsDataset, DATA_DIR, OUT_DIR, NUM_LABELS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ckpt = torch.load(OUT_DIR / "best_model.pt", map_location=device, weights_only=False)
print(f"Loaded checkpoint from epoch {ckpt['epoch']}, val_macro_f1={ckpt['val_macro_f1']:.4f}")

tokenizer = RobertaTokenizerFast.from_pretrained(ckpt["tokenizer_name"])
model = RobertaForSequenceClassification.from_pretrained(
    ckpt["tokenizer_name"],
    num_labels=NUM_LABELS,
    problem_type="multi_label_classification",
).to(device)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

val_ds = GoEmotionsDataset(DATA_DIR / "val.jsonl", tokenizer, max_length=128)
val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)

# Collect all probs once
all_probs, all_targets = [], []
with torch.no_grad():
    for batch in val_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        with autocast("cuda"):
            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
        all_probs.append(torch.sigmoid(logits).cpu().numpy())
        all_targets.append(batch["labels"].numpy())

all_probs = np.concatenate(all_probs, axis=0)
all_targets = np.concatenate(all_targets, axis=0).astype(int)

print("\nThreshold sweep on val set:\n")
print(f"{'thr':>5}  {'macro_F1':>9}  {'micro_F1':>9}")
print("-" * 30)
best = (-1, 0.3)
for thr in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]:
    preds = (all_probs >= thr).astype(int)
    macro = f1_score(all_targets, preds, average="macro", zero_division=0)
    micro = f1_score(all_targets, preds, average="micro", zero_division=0)
    print(f"{thr:>5.2f}  {macro:>9.4f}  {micro:>9.4f}")
    if macro > best[0]:
        best = (macro, thr)

print(f"\nBest macro_F1 = {best[0]:.4f} at threshold {best[1]:.2f}")