"""
Download and prepare the GoEmotions dataset for fine-tuning RoBERTa.

GoEmotions: 28 categories (27 emotions + neutral), multi-label.
Each example can have zero, one, or many labels.
"""

import json
from pathlib import Path
from collections import Counter

from datasets import load_dataset

OUT_DIR = Path(__file__).resolve().parent.parent / "data_processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GOEMOTIONS_LABELS = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral",
]


def save_split(dataset, split_name, out_dir):
    out_path = out_dir / f"{split_name}.jsonl"
    label_counts = Counter()
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in dataset:
            row = {
                "text": ex["text"],
                "labels": ex["labels"],
                "id": ex["id"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            for lbl in ex["labels"]:
                label_counts[GOEMOTIONS_LABELS[lbl]] += 1
            n += 1
    print(f"{split_name}: {n} examples -> {out_path}")
    return label_counts


def main():
    print("Downloading GoEmotions (simplified) from HuggingFace ...")
    ds = load_dataset("go_emotions", "simplified")
    print(ds)

    train_counts = save_split(ds["train"], "train", OUT_DIR)
    save_split(ds["validation"], "val", OUT_DIR)
    save_split(ds["test"], "test", OUT_DIR)

    print("\nTrain class distribution:")
    total = sum(train_counts.values())
    for label, count in sorted(train_counts.items(), key=lambda x: -x[1]):
        print(f"  {label:16s}  {count:6d}  ({100.0 * count / total:5.2f}%)")

    with open(OUT_DIR / "labels.json", "w", encoding="utf-8") as f:
        json.dump(GOEMOTIONS_LABELS, f, indent=2)

    print(f"\nDone. Output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()