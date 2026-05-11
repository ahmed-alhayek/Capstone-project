
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.amp import autocast
from transformers import RobertaTokenizerFast, RobertaForSequenceClassification
from sklearn.metrics import f1_score
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from train import GoEmotionsDataset, DATA_DIR, OUT_DIR, NUM_LABELS, LABELS

# Per-class thresholds — must match predict_v2.py (production inference)
PER_CLASS_THRESHOLD = {
    "sadness": 0.10,
    "disappointment": 0.10,
    "grief": 0.10,
    "fear": 0.10,
    "nervousness": 0.10,
    "remorse": 0.10,
}
DEFAULT_THRESHOLD = 0.20

# The 12 mental-health-relevant categories used by the fusion layer (highlighted in figure)
MH_RELEVANT_12 = {
    "joy", "excitement", "love", "sadness", "nervousness", "fear",
    "anger", "disappointment", "remorse", "embarrassment", "disgust", "neutral",
}


def collect_predictions(model, loader, device):
    """Run inference on a loader, return (probs, targets) as numpy arrays."""
    model.eval()
    device_type = "cuda" if device.type == "cuda" else "cpu"
    all_probs, all_targets = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            with autocast(device_type):
                logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
            all_probs.append(torch.sigmoid(logits).cpu().numpy())
            all_targets.append(batch["labels"].numpy())
    probs = np.concatenate(all_probs, axis=0)
    targets = np.concatenate(all_targets, axis=0).astype(int)
    return probs, targets


def apply_per_class_thresholds(probs):
    """Apply 0.10 to the six low-threshold emotions, 0.20 to the other 22."""
    preds = np.zeros_like(probs, dtype=int)
    for i, label in enumerate(LABELS):
        thr = PER_CLASS_THRESHOLD.get(label, DEFAULT_THRESHOLD)
        preds[:, i] = (probs[:, i] >= thr).astype(int)
    return preds


def compute_per_class_f1(targets, preds):
    return [
        f1_score(targets[:, i], preds[:, i], zero_division=0)
        for i in range(NUM_LABELS)
    ]


def plot_bar_chart(per_class_f1, split_name, out_path):
    macro_f1 = float(np.mean(per_class_f1))

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = [
        "#1f4e79" if label in MH_RELEVANT_12 else "#bbbbbb"
        for label in LABELS
    ]
    ax.bar(range(NUM_LABELS), per_class_f1, color=colors,
           edgecolor="black", linewidth=0.4)

    ax.set_xticks(range(NUM_LABELS))
    ax.set_xticklabels(LABELS, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("F1 score", fontsize=12)
    ax.set_xlabel("GoEmotions category", fontsize=12)
    ax.set_title(
        f"Per-class F1 on GoEmotions {split_name} set "
        f"(production text model, per-class thresholds)",
        fontsize=13,
    )
    ax.set_ylim(0, 1.0)
    ax.axhline(y=macro_f1, color="red", linestyle="--", alpha=0.6)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    legend_elements = [
        Patch(facecolor="#1f4e79", edgecolor="black",
              label="Mental-health-relevant (12 used by fusion)"),
        Patch(facecolor="#bbbbbb", edgecolor="black",
              label="Other GoEmotions labels"),
        Line2D([0], [0], color="red", linestyle="--", alpha=0.6,
               label=f"Macro-F1 = {macro_f1:.3f}"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved figure: {out_path}")


def evaluate_split(split_jsonl, split_name, model, tokenizer, device, out_dir):
    print(f"\n=== Evaluating on {split_name} set ===")
    ds = GoEmotionsDataset(split_jsonl, tokenizer, max_length=128)
    loader = DataLoader(ds, batch_size=32, shuffle=False)
    print(f"  {len(ds)} examples")

    probs, targets = collect_predictions(model, loader, device)
    preds = apply_per_class_thresholds(probs)

    per_class_f1 = compute_per_class_f1(targets, preds)
    macro_f1 = float(np.mean(per_class_f1))
    micro_f1 = float(f1_score(targets, preds, average="micro", zero_division=0))

    print(f"\n  Macro-F1: {macro_f1:.4f}")
    print(f"  Micro-F1: {micro_f1:.4f}")
    print(f"\n  Per-class F1 (canonical order, * = lowered 0.10 threshold, MH = in fusion 12):")
    print(f"  {'label':<18}  {'F1':>7}   tag")
    print(f"  {'-'*18}  {'-'*7}   ----")
    for i, label in enumerate(LABELS):
        tag = ""
        if label in PER_CLASS_THRESHOLD:
            tag += "*"
        else:
            tag += " "
        if label in MH_RELEVANT_12:
            tag += " MH"
        print(f"  {label:<18}  {per_class_f1[i]:>7.4f}   {tag}")

    fig_path = out_dir / f"per_class_f1_{split_name}.png"
    plot_bar_chart(per_class_f1, split_name, fig_path)

    json_path = out_dir / f"per_class_f1_{split_name}.json"
    with open(json_path, "w") as f:
        json.dump({
            "split": split_name,
            "macro_f1": macro_f1,
            "micro_f1": micro_f1,
            "per_class_f1": {LABELS[i]: per_class_f1[i] for i in range(NUM_LABELS)},
            "thresholds_used": {
                label: PER_CLASS_THRESHOLD.get(label, DEFAULT_THRESHOLD)
                for label in LABELS
            },
            "highlighted_in_figure": sorted(MH_RELEVANT_12),
        }, f, indent=2)
    print(f"  Saved JSON:   {json_path}")

    return macro_f1, micro_f1


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    ckpt_path = OUT_DIR / "best_model.pt"
    print(f"Loading checkpoint: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    print(f"  Trained at epoch {ckpt['epoch']}")
    print(f"  Stored val_macro_F1 (single-threshold during training): "
          f"{ckpt['val_macro_f1']:.4f}")

    tokenizer = RobertaTokenizerFast.from_pretrained(ckpt["tokenizer_name"])
    model = RobertaForSequenceClassification.from_pretrained(
        ckpt["tokenizer_name"],
        num_labels=NUM_LABELS,
        problem_type="multi_label_classification",
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    fig_out = OUT_DIR

    val_path = DATA_DIR / "val.jsonl"
    val_macro, val_micro = evaluate_split(val_path, "val", model, tokenizer, device, fig_out)

    test_path = DATA_DIR / "test.jsonl"
    if test_path.exists():
        test_macro, test_micro = evaluate_split(test_path, "test", model, tokenizer, device, fig_out)
    else:
        print(f"\n(test.jsonl not found at {test_path}, skipping test evaluation)")
        test_macro = test_micro = None

    print("\n" + "=" * 60)
    print("SUMMARY  (with production per-class thresholds applied)")
    print("=" * 60)
    print(f"Val:   macro_F1 = {val_macro:.4f}   micro_F1 = {val_micro:.4f}")
    if test_macro is not None:
        print(f"Test:  macro_F1 = {test_macro:.4f}   micro_F1 = {test_micro:.4f}")
    print("\nUse the PNGs as Figure 4.1 of the report.")
    print("Use the val/test macro_F1 and micro_F1 above to update Tables 4.1 and 4.2.\n")


if __name__ == "__main__":
    main()