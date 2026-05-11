"""
Predict emotions for text input using the fine-tuned RoBERTa model.
"""

import argparse
from pathlib import Path

import torch
from torch.amp import autocast
from transformers import RobertaTokenizerFast, RobertaForSequenceClassification

THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "saved_models" / "roberta_goemotions"
# Per-class thresholds: mental-health-relevant emotions detect at lower confidence
# because mild emotional language is often labeled as neutral in GoEmotions.
# Other emotions use the default global threshold.
PER_CLASS_THRESHOLD = {
    "sadness": 0.10,
    "disappointment": 0.10,
    "grief": 0.10,
    "fear": 0.10,
    "nervousness": 0.10,
    "remorse": 0.10,
}

_cache = {}


def load_model(ckpt_path=None):
    if _cache:
        return _cache
    if ckpt_path is None:
        ckpt_path = OUT_DIR / "best_model.pt"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)

    tokenizer = RobertaTokenizerFast.from_pretrained(ckpt["tokenizer_name"])
    model = RobertaForSequenceClassification.from_pretrained(
        ckpt["tokenizer_name"],
        num_labels=len(ckpt["labels"]),
        problem_type="multi_label_classification",
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    _cache.update({
        "model": model,
        "tokenizer": tokenizer,
        "labels": ckpt["labels"],
        "device": device,
    })
    return _cache


@torch.no_grad()
def predict(text, threshold=0.20, top_k=5):
    c = load_model()
    enc = c["tokenizer"](
        text, truncation=True, padding="max_length",
        max_length=128, return_tensors="pt",
    ).to(c["device"])

    autocast_device = "cuda" if c["device"].type == "cuda" else "cpu"
    with autocast(autocast_device):
        logits = c["model"](**enc).logits
    probs = torch.sigmoid(logits)[0].cpu().numpy()

    ranked = sorted(
        [(c["labels"][i], float(probs[i])) for i in range(len(probs))],
        key=lambda x: -x[1],
    )
    # Per-class thresholds for mental-health-relevant emotions, fallback to global threshold
    above = [
        (e, p) for e, p in ranked
        if p >= PER_CLASS_THRESHOLD.get(e, threshold)
    ]
    return {"above_threshold": above, "top_k": ranked[:top_k]}


def show(text, threshold):
    result = predict(text, threshold=threshold)
    print(f"\nText: {text}")
    if result["above_threshold"]:
        print("Detected:")
        for e, p in result["above_threshold"]:
            print(f"  {e:18s}  {p:.3f}")
    else:
        top1 = result["top_k"][0]
        print(f"(none above {threshold} — top emotion: {top1[0]} at {top1[1]:.3f})")
    print(f"Top 5: " + ", ".join(f"{e}({p:.2f})" for e, p in result["top_k"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, default=None)
    parser.add_argument("--threshold", type=float, default=0.20)
    args = parser.parse_args()

    if args.text:
        show(args.text, args.threshold)
        return

    print("\nText emotion predictor. Type a sentence (or 'quit'/'q' to exit).\n")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue
        show(text, args.threshold)
        print()


if __name__ == "__main__":
    main()