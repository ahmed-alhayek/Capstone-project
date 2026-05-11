"""
Fine-tune roberta-base on GoEmotions for multi-label emotion classification.
"""

import json
import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import autocast, GradScaler
from torch.optim import AdamW
from transformers import (
    RobertaTokenizerFast,
    RobertaForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import f1_score

THIS_DIR = Path(__file__).resolve().parent
DATA_DIR = THIS_DIR / "data_processed"
OUT_DIR = THIS_DIR / "saved_models" / "roberta_goemotions"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_DIR / "labels.json", "r") as f:
    LABELS = json.load(f)
NUM_LABELS = len(LABELS)


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class GoEmotionsDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=128):
        self.examples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                self.examples.append(json.loads(line))
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        enc = self.tokenizer(
            ex["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        labels_vec = torch.zeros(NUM_LABELS, dtype=torch.float)
        for lbl in ex["labels"]:
            labels_vec[lbl] = 1.0
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": labels_vec,
        }


def compute_pos_weight(jsonl_path):
    """Kept for reference — not used in run 2 (no class weighting)."""
    counts = np.zeros(NUM_LABELS)
    n = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            for lbl in ex["labels"]:
                counts[lbl] += 1
            n += 1
    pos_weight = (n - counts) / np.maximum(counts, 1.0)
    pos_weight = np.clip(pos_weight, 1.0, 5.0)
    return torch.tensor(pos_weight, dtype=torch.float)


@torch.no_grad()
def evaluate(model, loader, device, threshold=0.10):
    model.eval()
    all_preds, all_targets = [], []
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        with autocast():
            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
        probs = torch.sigmoid(logits)
        preds = (probs >= threshold).long().cpu().numpy()
        all_preds.append(preds)
        all_targets.append(labels.long().cpu().numpy())
    all_preds = np.concatenate(all_preds, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    micro_f1 = f1_score(all_targets, all_preds, average="micro", zero_division=0)
    return macro_f1, micro_f1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="roberta-base")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--grad_accum", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--warmup_ratio", type=float, default=0.1)
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--threshold", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--smoke_test", action="store_true")
    args = parser.parse_args()
    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print(f"Loading tokenizer + model: {args.model_name}")
    tokenizer = RobertaTokenizerFast.from_pretrained(args.model_name)
    model = RobertaForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=NUM_LABELS,
        problem_type="multi_label_classification",
    ).to(device)

    train_ds = GoEmotionsDataset(DATA_DIR / "train.jsonl", tokenizer, args.max_length)
    val_ds = GoEmotionsDataset(DATA_DIR / "val.jsonl", tokenizer, args.max_length)

    if args.smoke_test:
        train_ds.examples = train_ds.examples[:128]
        val_ds.examples = val_ds.examples[:64]
        args.epochs = 1
        print(f"SMOKE TEST: train={len(train_ds)}, val={len(val_ds)}, 1 epoch")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size,
                              shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2,
                            shuffle=False, num_workers=0, pin_memory=True)

    # Run 3: mild pos_weight (cap=5) — middle ground between run 1 and run 2
    pos_weight = compute_pos_weight(DATA_DIR / "train.jsonl").to(device)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = max((len(train_loader) // args.grad_accum) * args.epochs, 1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * args.warmup_ratio),
        num_training_steps=total_steps,
    )
    scaler = GradScaler()

    history = []
    best_macro_f1 = -1.0

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        optimizer.zero_grad(set_to_none=True)

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device, non_blocking=True)
            attention_mask = batch["attention_mask"].to(device, non_blocking=True)
            labels = batch["labels"].to(device, non_blocking=True)

            with autocast():
                logits = model(input_ids=input_ids,
                               attention_mask=attention_mask).logits
                loss = loss_fn(logits, labels) / args.grad_accum

            scaler.scale(loss).backward()
            running_loss += loss.item() * args.grad_accum

            if (step + 1) % args.grad_accum == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

            if (step + 1) % 100 == 0:
                print(f"epoch {epoch}  step {step+1}/{len(train_loader)}  "
                      f"loss {running_loss/(step+1):.4f}")

        macro_f1, micro_f1 = evaluate(model, val_loader, device, args.threshold)
        train_loss = running_loss / max(len(train_loader), 1)
        print(f"\nEpoch {epoch}: train_loss={train_loss:.4f}  "
              f"val_macro_f1={macro_f1:.4f}  val_micro_f1={micro_f1:.4f}\n")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_macro_f1": macro_f1,
            "val_micro_f1": micro_f1,
        })

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            ckpt_path = OUT_DIR / "best_model.pt"
            torch.save({
                "model_state_dict": model.state_dict(),
                "tokenizer_name": args.model_name,
                "labels": LABELS,
                "args": vars(args),
                "val_macro_f1": macro_f1,
                "val_micro_f1": micro_f1,
                "epoch": epoch,
            }, ckpt_path)
            print(f"Saved best model: {ckpt_path}  (macro_f1={macro_f1:.4f})")

    with open(OUT_DIR / "training_history.json", "w") as f:
        json.dump({
            "args": vars(args),
            "history": history,
            "best_val_macro_f1": best_macro_f1,
        }, f, indent=2)

    print(f"\nDone. Best val macro_f1: {best_macro_f1:.4f}")


if __name__ == "__main__":
    main()