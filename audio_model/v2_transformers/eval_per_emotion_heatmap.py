"""
Compute per-class F1 for Wav2Vec2, HuBERT, and WavLM on the test set,
then plot Figure 4.3: an 8-emotion x 3-architecture heatmap.

Forces HuggingFace offline mode at the very top to avoid the
"Server disconnected" network errors seen during the May 9-10 session.
This must be set BEFORE any transformers / huggingface_hub imports.

Run from audio_model/v2_transformers/:
    python eval_per_emotion_heatmap.py
"""

# ============================================================
# Force HuggingFace offline mode (must come before transformers imports)
# ============================================================
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# ============================================================
# Imports
# ============================================================
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

from sklearn.metrics import f1_score
from transformers import (
    Wav2Vec2FeatureExtractor,
    Wav2Vec2ForSequenceClassification, Wav2Vec2Config,
    HubertForSequenceClassification, HubertConfig,
    WavLMForSequenceClassification, WavLMConfig,
)

from audio_dataset import CachedAudioEmotionDataset, make_collate_fn

# ============================================================
# Config
# ============================================================
HERE = Path(__file__).resolve().parent
CACHE_DIR = Path.home() / "audio_cache_v2"
SAVED_DIR = HERE / "saved_models"

OUT_FIG = SAVED_DIR / "per_emotion_f1_heatmap.png"
OUT_JSON = SAVED_DIR / "per_emotion_f1_all.json"

EMOTIONS = [
    "neutral", "calm", "happy", "sad",
    "angry", "fearful", "disgust", "surprised",
]
NUM_CLASSES = len(EMOTIONS)

MODELS = [
    ("Wav2Vec2", "facebook/wav2vec2-base",
     Wav2Vec2ForSequenceClassification, Wav2Vec2Config,
     "wav2vec2/best_model.pt"),
    ("HuBERT",   "facebook/hubert-base-ls960",
     HubertForSequenceClassification, HubertConfig,
     "hubert/best_model.pt"),
    ("WavLM",    "microsoft/wavlm-base-plus",
     WavLMForSequenceClassification, WavLMConfig,
     "wavlm/best_model.pt"),
]


def load_one_model(model_name, model_class, config_class, weights_path, device):
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
    config = config_class.from_pretrained(model_name)
    config.num_labels = NUM_CLASSES
    config.id2label = {i: EMOTIONS[i] for i in range(NUM_CLASSES)}
    config.label2id = {EMOTIONS[i]: i for i in range(NUM_CLASSES)}
    model = model_class(config)
    state = torch.load(weights_path, map_location=device)
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


def evaluate_model(display_name, model_name, model_class, config_class,
                   weights_path, test_npz, device):
    print(f"\n=== Evaluating {display_name} ({model_name}) ===")
    model, feature_extractor = load_one_model(
        model_name, model_class, config_class, weights_path, device,
    )
    test_ds = CachedAudioEmotionDataset(test_npz)
    collate = make_collate_fn(feature_extractor)
    test_loader = DataLoader(
        test_ds, batch_size=8, shuffle=False,
        collate_fn=collate, num_workers=0, pin_memory=True,
    )
    preds, labels = run_inference(model, test_loader, device)

    per_class = f1_score(
        labels, preds, average=None,
        labels=list(range(NUM_CLASSES)),
        zero_division=0,
    )
    macro = float(f1_score(labels, preds, average="macro", zero_division=0))

    print(f"  Macro-F1: {macro:.4f}")
    for i, e in enumerate(EMOTIONS):
        print(f"    {e:<11} {per_class[i]:.4f}")

    del model
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return per_class, macro


def plot_heatmap(matrix, model_names, emotion_names, out_path):
    fig, ax = plt.subplots(figsize=(7.5, 7))
    im = ax.imshow(matrix, cmap="Blues", vmin=0.5, vmax=1.0, aspect="auto")

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.set_label("F1 score", fontsize=11)

    ax.set(
        xticks=np.arange(len(model_names)),
        yticks=np.arange(len(emotion_names)),
        xticklabels=model_names,
        yticklabels=emotion_names,
    )
    ax.set_xlabel("Architecture", fontsize=12)
    ax.set_ylabel("Emotion class", fontsize=12)
    ax.set_title(
        "Per-emotion F1 on the test set\n"
        "(8 emotion classes x 3 transformer architectures)",
        fontsize=12,
    )

    for i in range(len(emotion_names)):
        for j in range(len(model_names)):
            value = matrix[i, j]
            text_color = "white" if value > 0.85 else "black"
            ax.text(j, i, f"{value:.3f}", ha="center", va="center",
                    color=text_color, fontsize=11)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nSaved figure: {out_path}")


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    test_npz = CACHE_DIR / "test.npz"
    if not test_npz.exists():
        print(f"ERROR: test cache not found at {test_npz}")
        return

    results = {}
    per_emotion_matrix = []
    model_display_names = []

    for display_name, model_name, model_class, config_class, weights_subpath in MODELS:
        weights_path = SAVED_DIR / weights_subpath
        if not weights_path.exists():
            print(f"WARNING: weights not found at {weights_path}, skipping {display_name}")
            continue
        per_class, macro = evaluate_model(
            display_name, model_name, model_class, config_class,
            weights_path, test_npz, device,
        )
        per_emotion_matrix.append(per_class)
        results[display_name] = {
            "model_name": model_name,
            "macro_f1": macro,
            "per_class_f1": {EMOTIONS[i]: float(per_class[i]) for i in range(NUM_CLASSES)},
        }
        model_display_names.append(display_name)

    if not per_emotion_matrix:
        print("No models were evaluated successfully.")
        return

    matrix = np.array(per_emotion_matrix).T
    plot_heatmap(matrix, model_display_names, EMOTIONS, OUT_FIG)

    with open(OUT_JSON, "w") as f:
        json.dump({
            "emotion_labels": EMOTIONS,
            "results": results,
        }, f, indent=2)
    print(f"Saved JSON:    {OUT_JSON}")

    print("\n" + "=" * 70)
    print("PER-EMOTION F1 SUMMARY (test set)")
    print("=" * 70)
    header = f"{'Emotion':<12}" + "".join(f"{n:>12}" for n in model_display_names)
    print(header)
    print("-" * len(header))
    for i, e in enumerate(EMOTIONS):
        row = f"{e:<12}"
        for j in range(len(model_display_names)):
            row += f"{matrix[i, j]:>12.4f}"
        print(row)
    print("-" * len(header))
    macros = f"{'Macro-F1':<12}" + "".join(
        f"{results[n]['macro_f1']:>12.4f}" for n in model_display_names
    )
    print(macros)
    print(f"\nUse {OUT_FIG.name} as Figure 4.3 in the report.")


if __name__ == "__main__":
    main()