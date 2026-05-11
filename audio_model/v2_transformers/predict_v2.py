"""
Phase 2C inference module for the backend.

Loads the fine-tuned HuBERT model once at import time, then exposes
a predict_emotion(audio_bytes_or_path) function that returns the
same 8-emotion vector format as Phase 1 (so fusion.py works unchanged).
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Union

import numpy as np
import torch
import torchaudio
from transformers import (
    Wav2Vec2FeatureExtractor,
    HubertForSequenceClassification,
    HubertConfig,
)


# ============================================================
# Config
# ============================================================
HERE = Path(__file__).resolve().parent
MODEL_NAME = "facebook/hubert-base-ls960"
WEIGHTS_PATH = HERE / "saved_models" / "hubert" / "best_model.pt"

TARGET_SR = 16000
MAX_SECONDS = 4.0
MAX_SAMPLES = int(TARGET_SR * MAX_SECONDS)

# Same 8-emotion ordering as Phase 1 (RAVDESS native order)
EMOTIONS = [
    "neutral", "calm", "happy", "sad",
    "angry", "fearful", "disgust", "surprised",
]
NUM_CLASSES = len(EMOTIONS)


# ============================================================
# Lazy module-level singletons (loaded once)
# ============================================================
_DEVICE = None
_MODEL = None
_FEAT_EXTRACTOR = None


def _ensure_loaded():
    global _DEVICE, _MODEL, _FEAT_EXTRACTOR
    if _MODEL is not None:
        return
    _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[predict_v2] Loading HuBERT on {_DEVICE}...")

    _FEAT_EXTRACTOR = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)

    # Build the architecture from config alone. We don't need the base model
    # weights from HuggingFace because our fine-tuned checkpoint contains
    # every parameter and overwrites the random init via load_state_dict.
    config = HubertConfig.from_pretrained(MODEL_NAME)
    config.num_labels = NUM_CLASSES
    config.id2label = {i: EMOTIONS[i] for i in range(NUM_CLASSES)}
    config.label2id = {EMOTIONS[i]: i for i in range(NUM_CLASSES)}
    _MODEL = HubertForSequenceClassification(config)

    # Load our Phase 2C fine-tuned weights.
    state = torch.load(WEIGHTS_PATH, map_location=_DEVICE)
    _MODEL.load_state_dict(state)
    _MODEL.to(_DEVICE)
    _MODEL.eval()
    print(f"[predict_v2] Ready.")


# ============================================================
# Audio preprocessing
# ============================================================
def _load_waveform(audio: Union[str, Path, bytes, np.ndarray]) -> np.ndarray:
    """Accepts a file path, raw bytes (e.g. uploaded WAV/WebM), or float32 array."""
    if isinstance(audio, (str, Path)):
        waveform, sr = torchaudio.load(str(audio))
    elif isinstance(audio, (bytes, bytearray)):
        waveform, sr = torchaudio.load(io.BytesIO(audio))
    elif isinstance(audio, np.ndarray):
        return _fit_length(audio.astype(np.float32))
    else:
        raise TypeError(f"Unsupported audio type: {type(audio)}")

    # mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    # resample
    if sr != TARGET_SR:
        waveform = torchaudio.functional.resample(waveform, sr, TARGET_SR)

    return _fit_length(waveform.squeeze(0).numpy().astype(np.float32))


def _fit_length(wav: np.ndarray) -> np.ndarray:
    if len(wav) > MAX_SAMPLES:
        start = (len(wav) - MAX_SAMPLES) // 2
        return wav[start:start + MAX_SAMPLES]
    if len(wav) < MAX_SAMPLES:
        return np.pad(wav, (0, MAX_SAMPLES - len(wav)))
    return wav


# ============================================================
# Public API
# ============================================================
def predict_emotion(audio: Union[str, Path, bytes, np.ndarray]) -> dict:
    """Run HuBERT inference on a single audio sample.

    Returns a dict with the same shape Phase 1 used so backend/fusion.py
    needs no changes:

        {
          "emotions": {"neutral": 0.02, "calm": 0.01, ..., "surprised": 0.05},
          "dominant_emotion": "happy",
          "confidence": 0.87,
          "model": "hubert-base-ls960-phase2c",
        }
    """
    _ensure_loaded()
    wav = _load_waveform(audio)

    inputs = _FEAT_EXTRACTOR(
        [wav],
        sampling_rate=TARGET_SR,
        return_tensors="pt",
        padding=True,
    )
    input_values = inputs.input_values.to(_DEVICE)

    with torch.no_grad():
        with torch.amp.autocast("cuda", enabled=_DEVICE.type == "cuda"):
            logits = _MODEL(input_values).logits
        probs = torch.softmax(logits.float(), dim=-1).cpu().numpy()[0]

    emo_dict = {EMOTIONS[i]: float(probs[i]) for i in range(NUM_CLASSES)}
    top_idx = int(probs.argmax())
    return {
        "emotions": emo_dict,
        "dominant_emotion": EMOTIONS[top_idx],
        "confidence": float(probs[top_idx]),
        "model": "hubert-base-ls960-phase2c",
    }


# ============================================================
# CLI smoke test
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict_v2.py <path_to_wav>")
        sys.exit(1)
    result = predict_emotion(sys.argv[1])
    print(f"\nDominant: {result['dominant_emotion']} "
          f"(conf={result['confidence']:.3f})")
    print(f"Model: {result['model']}")
    print("All emotions:")
    for emo, p in sorted(result["emotions"].items(), key=lambda x: -x[1]):
        bar = "#" * int(p * 40)
        print(f"  {emo:<11} {p:.4f}  {bar}")