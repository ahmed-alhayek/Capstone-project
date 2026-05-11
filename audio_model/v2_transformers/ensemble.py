"""
Phase 2C - Ensemble of Wav2Vec2 + HuBERT + WavLM.

Loads all 3 fine-tuned models, computes softmax probabilities on the
test set, and averages them with weights proportional to each model's
validation accuracy.
"""

import sys
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import (
    Wav2Vec2FeatureExtractor,
    Wav2Vec2ForSequenceClassification,
    HubertForSequenceClassification,
    WavLMForSequenceClassification,
)
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "data"))
sys.path.insert(0, str(HERE))

from unified_loader import EMOTIONS, NUM_CLASSES
from audio_dataset import CachedAudioEmotionDataset, make_collate_fn


CACHE_DIR = Path.home() / "audio_cache_v2"
SAVED_DIR = HERE / "saved_models"
BATCH_SIZE = 8

MODELS_CFG = [
    {
        "name": "wav2vec2",
        "hf_name": "facebook/wav2vec2-base",
        "cls": Wav2Vec2ForSequenceClassification,
        "weights": SAVED_DIR / "wav2vec2" / "best_model.pt",
        "results": SAVED_DIR / "wav2vec2" / "test_results.json",
    },
    {
        "name": "hubert",
        "hf_name": "facebook/hubert-base-ls960",
        "cls": HubertForSequenceClassification,
        "weights": SAVED_DIR / "hubert" / "best_model.pt",
        "results": SAVED_DIR / "hubert" / "test_results.json",
    },
    {
        "name": "wavlm",
        "hf_name": "microsoft/wavlm-base-plus",
        "cls": WavLMForSequenceClassification,
        "weights": SAVED_DIR / "wavlm" / "best_model.pt",
        "results": SAVED_DIR / "wavlm" / "test_results.json",
    },
]


def get_softmax_probs(model_cfg, loader, device):
    """Run a model on the loader and return softmax probabilities + labels."""
    print(f"\nRunning {model_cfg['name']}...")
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_cfg["hf_name"])
    collate = make_collate_fn(feature_extractor)

    model = model_cfg["cls"].from_pretrained(
        model_cfg["hf_name"],
        num_labels=NUM_CLASSES,
        id2label={i: EMOTIONS[i] for i in range(NUM_CLASSES)},
        label2id={EMOTIONS[i]: i for i in range(NUM_CLASSES)},
        use_safetensors=True,
    )
    state = torch.load(model_cfg["weights"], map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    # Re-create the loader with this model's collate function
    fresh_loader = DataLoader(
        loader.dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=collate,
        num_workers=0,
        pin_memory=True,
    )

    all_probs, all_labels = [], []
    with torch.no_grad():
        for input_values, y in fresh_loader:
            input_values = input_values.to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(input_values).logits
            probs = torch.softmax(logits.float(), dim=-1).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(y.numpy())

    # Free GPU memory before loading next model
    del model
    torch.cuda.empty_cache()

    return np.concatenate(all_probs), np.concatenate(all_labels)


def report_metrics(name, preds, labels):
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="macro")
    print(f"  {name}: acc={acc:.4f}  macro_f1={f1:.4f}")
    return acc, f1


def print_confusion(name, preds, labels):
    cm = confusion_matrix(labels, preds, labels=list(range(NUM_CLASSES)))
    print(f"\n{name} confusion matrix (rows=true, cols=pred):")
    header = " " * 12 + " ".join(f"{EMOTIONS[i][:4]:>5}" for i in range(NUM_CLASSES))
    print(header)
    for i in range(NUM_CLASSES):
        print(f"  {EMOTIONS[i]:<10} " + " ".join(f"{cm[i,j]:>5}" for j in range(NUM_CLASSES)))


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    test_ds = CachedAudioEmotionDataset(CACHE_DIR / "test.npz")
    # Use any feature extractor for the initial loader; will be replaced inside loop
    init_collate = make_collate_fn(
        Wav2Vec2FeatureExtractor.from_pretrained(MODELS_CFG[0]["hf_name"])
    )
    test_loader = DataLoader(
        test_ds, batch_size=BATCH_SIZE, shuffle=False,
        collate_fn=init_collate, num_workers=0, pin_memory=True,
    )

    # Load each model's val_acc to use as ensemble weight
    val_accs = []
    for cfg in MODELS_CFG:
        with open(cfg["results"]) as f:
            val_accs.append(json.load(f)["best_val_accuracy"])
    weights = np.array(val_accs) / sum(val_accs)
    print("\nEnsemble weights (based on best val accuracy):")
    for cfg, w in zip(MODELS_CFG, weights):
        print(f"  {cfg['name']:<10} {w:.4f}")

    # Run inference for each model
    all_probs = []
    labels_ref = None
    for cfg in MODELS_CFG:
        probs, labels = get_softmax_probs(cfg, test_loader, device)
        all_probs.append(probs)
        if labels_ref is None:
            labels_ref = labels
        else:
            assert np.array_equal(labels_ref, labels), "label mismatch across models"

    # Individual model accuracies
    print("\n=== INDIVIDUAL MODEL TEST RESULTS ===")
    for cfg, probs in zip(MODELS_CFG, all_probs):
        preds = probs.argmax(axis=1)
        report_metrics(cfg["name"], preds, labels_ref)

    # Weighted ensemble
    ensemble_probs = np.zeros_like(all_probs[0])
    for w, probs in zip(weights, all_probs):
        ensemble_probs += w * probs
    ensemble_preds = ensemble_probs.argmax(axis=1)

    print("\n=== ENSEMBLE TEST RESULTS ===")
    ens_acc, ens_f1 = report_metrics("ensemble", ensemble_preds, labels_ref)
    print_confusion("ensemble", ensemble_preds, labels_ref)

    # Save ensemble metadata so backend/predict_v2 can use it later
    out = {
        "ensemble_test_accuracy": float(ens_acc),
        "ensemble_test_macro_f1": float(ens_f1),
        "weights": {cfg["name"]: float(w) for cfg, w in zip(MODELS_CFG, weights)},
        "individual_test_accuracy": {
            cfg["name"]: float(accuracy_score(labels_ref, probs.argmax(1)))
            for cfg, probs in zip(MODELS_CFG, all_probs)
        },
    }
    out_path = SAVED_DIR / "ensemble_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()