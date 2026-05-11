"""
Compute and plot the confusion matrix and per-class F1 for HuBERT on the
held-out test set. Saves Figure 4.2 of the report (two versions: row-normalized
and raw counts), plus a JSON dump of all per-class metrics that will be
reused for Figure 4.3 (per-emotion F1 across the three transformers).

Run from audio_model/v2_transformers/:
    python eval_confusion_matrix.py
"""
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, classification_report,
)
from transformers import (
    Wav2Vec2FeatureExtractor,
    HubertForSequenceClassification,
    HubertConfig,
)

from audio_dataset import CachedAudioEmotionDataset, make_collate_fn

# ============================================================
# Config
# ============================================================
HERE = Path(__file__).resolve().parent
MODEL_NAME = "facebook/hubert-base-ls960"
WEIGHTS_PATH = HERE / "saved_models" / "hubert" / "best_model.pt"
CACHE_DIR = Path.home() / "audio_cache_v2"
OUT_DIR = HERE / "saved_models" / "hubert"

# Same canonical ordering as predict_v2.py
EMOTIONS = [
    "neutral", "calm", "happy", "sad",
    "angry", "fearful", "disgust", "surprised",
]
NUM_CLASSES = len(EMOTIONS)


def load_model(device):
    """Same loading pattern as predict_v2.py: build from config, then load_state_dict."""
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
    config = HubertConfig.from_pretrained(MODEL_NAME)
    config.num_labels = NUM_CLASSES
    config.id2label = {i: EMOTIONS[i] for i in range(NUM_CLASSES)}
    config.label2id = {EMOTIONS[i]: i for i in range(NUM_CLASSES)}
    model = HubertForSequenceClassification(config)
    state = torch.load(WEIGHTS_PATH, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, feature_extractor


def run_inference(model, loader, device):
    preds, labels = [], []
    with torch.no_grad():
        for input_values, y in loader:
            input_values = input_values.to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(input_values).logits
            preds.extend(logits.argmax(-1).cpu().numpy())
            labels.extend(y.numpy())
    return np.array(preds), np.array(labels)


def plot_confusion_matrix(cm, class_names, out_path, normalize=True):
    if normalize:
        cm_to_plot = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
        title_suffix = " (row-normalized: each row sums to 100%)"
        cmax = 1.0
    else:
        cm_to_plot = cm.astype(int)
        title_suffix = " (raw counts)"
        cmax = max(int(cm.max()), 1)

    fig, ax = plt.subplots(figsize=(9, 7.5))
    im = ax.imshow(cm_to_plot, interpolation="nearest", cmap="Blues",
                   vmin=0, vmax=cmax)

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.tick_params(labelsize=10)

    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
    )
    ax.set_xlabel("Predicted emotion", fontsize=12)
    ax.set_ylabel("True emotion", fontsize=12)
    ax.set_title(
        f"HuBERT confusion matrix on the test set{title_suffix}",
        fontsize=12,
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right",
             rotation_mode="anchor")

    threshold = cmax * 0.5
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            value = cm_to_plot[i, j]
            text_color = "white" if value > threshold else "black"
            if normalize:
                text = f"{value*100:.1f}%" if value >= 0.005 else "0"
            else:
                text = f"{int(value)}"
            ax.text(j, i, text, ha="center", va="center",
                    color=text_color, fontsize=9)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved figure: {out_path}")


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    print(f"\nLoading HuBERT from {WEIGHTS_PATH}")
    model, feature_extractor = load_model(device)

    test_npz = CACHE_DIR / "test.npz"
    print(f"Loading test cache from {test_npz}")
    test_ds = CachedAudioEmotionDataset(test_npz)
    collate = make_collate_fn(feature_extractor)
    test_loader = DataLoader(
        test_ds, batch_size=8, shuffle=False,
        collate_fn=collate, num_workers=0, pin_memory=True,
    )

    print(f"\nRunning inference on {len(test_ds)} test samples...")
    preds, labels = run_inference(model, test_loader, device)

    test_acc = accuracy_score(labels, preds)
    test_macro_f1 = f1_score(labels, preds, average="macro")
    test_micro_f1 = f1_score(labels, preds, average="micro")
    print(f"\nTest accuracy:  {test_acc:.4f}")
    print(f"Test macro-F1:  {test_macro_f1:.4f}")
    print(f"Test micro-F1:  {test_micro_f1:.4f}")

    print(f"\nPer-class report (test set):")
    print(classification_report(
        labels, preds,
        labels=list(range(NUM_CLASSES)),
        target_names=EMOTIONS,
        digits=4,
        zero_division=0,
    ))

    cm = confusion_matrix(labels, preds, labels=list(range(NUM_CLASSES)))
    print(f"Confusion matrix (rows = true, cols = predicted):")
    header = " " * 12 + " ".join(f"{e[:5]:>6}" for e in EMOTIONS)
    print(header)
    for i in range(NUM_CLASSES):
        row = " ".join(f"{cm[i,j]:>6}" for j in range(NUM_CLASSES))
        print(f"  {EMOTIONS[i]:<10} {row}")

    fig_norm = OUT_DIR / "confusion_matrix_normalized.png"
    fig_raw = OUT_DIR / "confusion_matrix_counts.png"
    plot_confusion_matrix(cm, EMOTIONS, fig_norm, normalize=True)
    plot_confusion_matrix(cm, EMOTIONS, fig_raw, normalize=False)

    per_class_f1 = f1_score(
        labels, preds, average=None,
        labels=list(range(NUM_CLASSES)),
        zero_division=0,
    )
    metrics = {
        "model": "hubert-base-ls960 (production)",
        "test_accuracy": float(test_acc),
        "test_macro_f1": float(test_macro_f1),
        "test_micro_f1": float(test_micro_f1),
        "per_class_f1": {EMOTIONS[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)},
        "confusion_matrix": cm.tolist(),
        "emotion_labels": EMOTIONS,
        "n_test_samples": int(len(labels)),
    }
    json_path = OUT_DIR / "test_metrics_detailed.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved JSON: {json_path}")
    print(f"\nUse {fig_norm.name} as Figure 4.2 in the report.")
    print(f"Per-class F1 written to JSON for Figure 4.3 input.")


if __name__ == "__main__":
    main()