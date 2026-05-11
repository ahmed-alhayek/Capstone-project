"""
One-time preprocessing: load all WAVs, resample to 16kHz, pad/crop to 4s,
save as numpy arrays on LOCAL disk (outside OneDrive).

For TRAIN split: applies 4x audio augmentation (noise, pitch, time, gain)
to combat overfitting on transformers.
"""

import sys
from pathlib import Path
import numpy as np
import torch
import torchaudio
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "data"))
from unified_loader import load_all, split_samples

AUDIO_ROOT = HERE.parent
CACHE_DIR = Path.home() / "audio_cache_v2"
CACHE_DIR.mkdir(exist_ok=True)

TARGET_SR = 16000
MAX_SECONDS = 4.0
MAX_SAMPLES = int(TARGET_SR * MAX_SECONDS)
N_AUG = 4  # augmentations per training sample (5x effective data: 1 original + 4 aug)
RNG = np.random.default_rng(42)


def load_and_normalize(path):
    waveform, sr = torchaudio.load(path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != TARGET_SR:
        waveform = torchaudio.functional.resample(waveform, sr, TARGET_SR)
    wav = waveform.squeeze(0).numpy().astype(np.float32)
    if len(wav) > MAX_SAMPLES:
        start = (len(wav) - MAX_SAMPLES) // 2
        wav = wav[start:start + MAX_SAMPLES]
    elif len(wav) < MAX_SAMPLES:
        wav = np.pad(wav, (0, MAX_SAMPLES - len(wav)))
    return wav


def add_noise(wav):
    snr_db = RNG.uniform(15, 30)
    sig_power = np.mean(wav ** 2) + 1e-9
    noise_power = sig_power / (10 ** (snr_db / 10))
    noise = RNG.normal(0, np.sqrt(noise_power), wav.shape).astype(np.float32)
    return wav + noise


def time_shift(wav):
    shift = RNG.integers(-TARGET_SR // 4, TARGET_SR // 4)
    return np.roll(wav, shift)


def pitch_shift(wav):
    n_steps = RNG.uniform(-2.0, 2.0)
    t = torch.from_numpy(wav).unsqueeze(0)
    out = torchaudio.functional.pitch_shift(t, TARGET_SR, n_steps)
    return out.squeeze(0).numpy().astype(np.float32)


def gain_perturb(wav):
    gain = RNG.uniform(0.7, 1.3)
    return wav * gain


def apply_random_aug(wav):
    """Pick 1-3 augmentations randomly and stack them."""
    augs = [add_noise, time_shift, gain_perturb]
    # pitch_shift is heavier (slow), use less often
    if RNG.random() < 0.5:
        augs.append(pitch_shift)
    n = RNG.integers(1, len(augs) + 1)
    chosen = RNG.choice(augs, size=n, replace=False)
    out = wav.copy()
    for fn in chosen:
        out = fn(out)
    # safety: clip
    return np.clip(out, -1.0, 1.0).astype(np.float32)


def cache_split(samples, name, augment=False):
    print(f"\nCaching {name} split ({len(samples)} samples"
          f"{f', {N_AUG}x augmentation' if augment else ''})...")
    multiplier = 1 + N_AUG if augment else 1
    total = len(samples) * multiplier
    waveforms = np.zeros((total, MAX_SAMPLES), dtype=np.float32)
    labels = np.zeros(total, dtype=np.int64)
    idx = 0
    for s in tqdm(samples):
        base = load_and_normalize(s.path)
        waveforms[idx] = base
        labels[idx] = s.label
        idx += 1
        if augment:
            for _ in range(N_AUG):
                waveforms[idx] = apply_random_aug(base)
                labels[idx] = s.label
                idx += 1
    out_path = CACHE_DIR / f"{name}.npz"
    np.savez(out_path, waveforms=waveforms, labels=labels)
    print(f"Saved {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)  "
          f"final size={total} samples")


def main():
    print(f"Cache dir: {CACHE_DIR}")
    samples = load_all(AUDIO_ROOT)
    train, val, test = split_samples(samples)
    print(f"  train={len(train)} val={len(val)} test={len(test)}")
    cache_split(train, "train", augment=True)   # 4240 -> 21,200
    cache_split(val, "val", augment=False)
    cache_split(test, "test", augment=False)
    total_mb = sum(f.stat().st_size for f in CACHE_DIR.glob("*.npz")) / 1e6
    print(f"\nDone. Total cache size: {total_mb:.1f} MB")


if __name__ == "__main__":
    main()