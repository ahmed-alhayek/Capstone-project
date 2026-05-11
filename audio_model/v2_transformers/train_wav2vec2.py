"""
Phase 2C - Train Wav2Vec2-base for 8-way speech emotion classification.
Uses pre-cached audio (run cache_audio.py first).
"""

import sys
import time
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import (
    Wav2Vec2FeatureExtractor,
    Wav2Vec2ForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "data"))
sys.path.insert(0, str(HERE))

from unified_loader import EMOTIONS, NUM_CLASSES
from audio_dataset import CachedAudioEmotionDataset, make_collate_fn


# ------------------ CONFIG ------------------
MODEL_NAME = "facebook/wav2vec2-base"
CACHE_DIR = Path.home() / "audio_cache_v2"

OUT_DIR = HERE / "saved_models" / "wav2vec2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_EPOCHS = 20
BATCH_SIZE = 8
GRAD_ACCUM = 1
LR = 1e-5           
WEIGHT_DECAY = 0.01
WARMUP_PCT = 0.10
EARLY_STOP_PATIENCE = 4
SEED = 42


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def evaluate(model, loader, device):
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for input_values, y in loader:
            input_values = input_values.to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(input_values).logits
            preds.extend(logits.argmax(-1).cpu().numpy())
            labels.extend(y.numpy())
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="macro")
    return acc, f1, np.array(preds), np.array(labels)


def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("\nLoading cached datasets...")
    train_ds = CachedAudioEmotionDataset(CACHE_DIR / "train.npz")
    val_ds = CachedAudioEmotionDataset(CACHE_DIR / "val.npz")
    test_ds = CachedAudioEmotionDataset(CACHE_DIR / "test.npz")

    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(NUM_CLASSES),
        y=train_ds.labels,
    )
    print("\nClass weights:")
    for i in range(NUM_CLASSES):
        print(f"  {EMOTIONS[i]:<11} {weights[i]:.3f}")
    class_weights = torch.tensor(weights, dtype=torch.float32, device=device)

    print(f"\nLoading {MODEL_NAME}...")
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
    model = Wav2Vec2ForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_CLASSES,
        id2label={i: EMOTIONS[i] for i in range(NUM_CLASSES)},
        label2id={EMOTIONS[i]: i for i in range(NUM_CLASSES)},
        use_safetensors=True,
    )
    
    model.to(device)

    collate = make_collate_fn(feature_extractor)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              collate_fn=collate, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            collate_fn=collate, num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             collate_fn=collate, num_workers=0, pin_memory=True)

    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    total_steps = (len(train_loader) // GRAD_ACCUM) * NUM_EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * WARMUP_PCT),
        num_training_steps=total_steps,
    )
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    best_val_acc = 0.0
    epochs_no_improve = 0
    history = []

    for epoch in range(1, NUM_EPOCHS + 1):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        optimizer.zero_grad()
        for step, (input_values, y) in enumerate(train_loader):
            input_values = input_values.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(input_values).logits
                loss = loss_fn(logits, y) / GRAD_ACCUM
            scaler.scale(loss).backward()
            running_loss += loss.item() * GRAD_ACCUM
            if (step + 1) % GRAD_ACCUM == 0:
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()

        train_loss = running_loss / len(train_loader)
        val_acc, val_f1, _, _ = evaluate(model, val_loader, device)
        elapsed = time.time() - t0
        print(f"Epoch {epoch:>2}/{NUM_EPOCHS}  "
              f"train_loss={train_loss:.4f}  val_acc={val_acc:.4f}  "
              f"val_f1={val_f1:.4f}  ({elapsed:.0f}s)")
        history.append({"epoch": epoch, "train_loss": train_loss,
                        "val_acc": val_acc, "val_f1": val_f1})

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            epochs_no_improve = 0
            torch.save(model.state_dict(), OUT_DIR / "best_model.pt")
            print(f"  -> new best, saved.")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= EARLY_STOP_PATIENCE:
                print(f"Early stopping (no improvement for {EARLY_STOP_PATIENCE} epochs).")
                break

    print("\nLoading best weights for test eval...")
    model.load_state_dict(torch.load(OUT_DIR / "best_model.pt"))
    test_acc, test_f1, test_preds, test_labels = evaluate(model, test_loader, device)
    print(f"\n=== TEST RESULTS ===")
    print(f"  accuracy: {test_acc:.4f}")
    print(f"  macro F1: {test_f1:.4f}")
    cm = confusion_matrix(test_labels, test_preds, labels=list(range(NUM_CLASSES)))
    print(f"  confusion matrix (rows=true, cols=pred):")
    header = " " * 12 + " ".join(f"{EMOTIONS[i][:4]:>5}" for i in range(NUM_CLASSES))
    print(header)
    for i in range(NUM_CLASSES):
        print(f"  {EMOTIONS[i]:<10} " + " ".join(f"{cm[i,j]:>5}" for j in range(NUM_CLASSES)))

    with open(OUT_DIR / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    with open(OUT_DIR / "test_results.json", "w") as f:
        json.dump({
            "test_accuracy": float(test_acc),
            "test_macro_f1": float(test_f1),
            "best_val_accuracy": float(best_val_acc),
            "model_name": MODEL_NAME,
            "epochs_run": len(history),
        }, f, indent=2)
    print(f"\nSaved: {OUT_DIR}")


if __name__ == "__main__":
    main()