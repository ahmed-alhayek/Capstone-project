"""
Unified data loader for Phase 2C audio model training.

Combines RAVDESS, TESS, and SAVEE into a single sample format with:
- Unified 8-emotion label space (RAVDESS native ordering)
- Globally unique actor IDs across all datasets
- Stratified random train/val/test split (Pepino 2021, Chen 2022,
  Morais 2022 evaluation protocol)

Usage:
    from unified_loader import load_all, split_samples
    samples = load_all("path/to/audio_model")  # dir containing RAVDESS/, TESS/, SAVEE/
    train, val, test = split_samples(samples)
"""

from __future__ import annotations
import re
import random
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


# ============================================================
# Unified label space (8 emotions, RAVDESS native ordering)
# ============================================================
EMOTIONS = {
    0: "neutral",
    1: "calm",       # RAVDESS only
    2: "happy",
    3: "sad",
    4: "angry",
    5: "fearful",
    6: "disgust",
    7: "surprised",
}
EMOTION_TO_ID = {v: k for k, v in EMOTIONS.items()}
NUM_CLASSES = len(EMOTIONS)


# ============================================================
# Globally unique actor IDs:
#   RAVDESS: 1-24    (native, odd=M, even=F)
#   TESS:    25 (OAF, F), 26 (YAF, F)
#   SAVEE:   27 (DC, M), 28 (JE, M), 29 (JK, M), 30 (KL, M)
# ============================================================


@dataclass
class AudioSample:
    path: str
    label: int            # 0..7
    label_name: str
    actor_id: int         # globally unique
    dataset: str          # "ravdess" | "tess" | "savee"
    speaker_gender: str   # "M" | "F"


# ============================================================
# RAVDESS
# ============================================================
# Filename: 03-01-06-01-02-01-12.wav
#   pos 3 = emotion (01..08)
#   pos 7 = actor (1..24)
RAVDESS_EMOTION_MAP = {
    "01": 0,  # neutral
    "02": 1,  # calm
    "03": 2,  # happy
    "04": 3,  # sad
    "05": 4,  # angry
    "06": 5,  # fearful
    "07": 6,  # disgust
    "08": 7,  # surprised
}


def load_ravdess(root: Path) -> List[AudioSample]:
    samples = []
    if not root.exists():
        print(f"[load_ravdess] WARN: path does not exist: {root}")
        return samples
    for wav in root.rglob("*.wav"):
        parts = wav.stem.split("-")
        if len(parts) != 7:
            continue
        emotion_code = parts[2]
        try:
            actor_num = int(parts[6])
        except ValueError:
            continue
        if emotion_code not in RAVDESS_EMOTION_MAP:
            continue
        label = RAVDESS_EMOTION_MAP[emotion_code]
        gender = "M" if actor_num % 2 == 1 else "F"
        samples.append(AudioSample(
            path=str(wav),
            label=label,
            label_name=EMOTIONS[label],
            actor_id=actor_num,
            dataset="ravdess",
            speaker_gender=gender,
        ))
    return samples


# ============================================================
# TESS
# ============================================================
# Folders like: OAF_angry, YAF_pleasant_surprised, OAF_Sad
# (case is inconsistent across folder names in this Kaggle release)
TESS_EMOTION_FOLDER_MAP = {
    "angry": 4,
    "disgust": 6,
    "fear": 5,
    "happy": 2,
    "neutral": 0,
    "pleasant_surprise": 7,
    "pleasant_surprised": 7,
    "sad": 3,
}


def load_tess(root: Path) -> List[AudioSample]:
    samples = []
    if not root.exists():
        print(f"[load_tess] WARN: path does not exist: {root}")
        return samples
    for wav in root.rglob("*.wav"):
        folder = wav.parent.name
        m = re.match(r"^(OAF|YAF)_(.+)$", folder, re.IGNORECASE)
        if not m:
            continue
        speaker = m.group(1).upper()
        emotion_str = m.group(2).lower()
        if emotion_str not in TESS_EMOTION_FOLDER_MAP:
            continue
        label = TESS_EMOTION_FOLDER_MAP[emotion_str]
        actor_id = 25 if speaker == "OAF" else 26
        samples.append(AudioSample(
            path=str(wav),
            label=label,
            label_name=EMOTIONS[label],
            actor_id=actor_id,
            dataset="tess",
            speaker_gender="F",
        ))
    return samples


# ============================================================
# SAVEE
# ============================================================
# Filenames look like:  DC_a01.wav, KL_su15.wav, JE_sa03.wav
# Emotion prefixes: a=anger, d=disgust, f=fear, h=happy,
#                   n=neutral, sa=sadness, su=surprise
# IMPORTANT: 'su' and 'sa' must be checked before 's' (longest match wins)
SAVEE_SPEAKER_MAP = {"DC": 27, "JE": 28, "JK": 29, "KL": 30}
SAVEE_EMOTION_PREFIXES = [
    ("su", 7),  # surprise
    ("sa", 3),  # sadness
    ("a", 4),   # anger
    ("d", 6),   # disgust
    ("f", 5),   # fear
    ("h", 2),   # happy
    ("n", 0),   # neutral
]


def load_savee(root: Path) -> List[AudioSample]:
    samples = []
    if not root.exists():
        print(f"[load_savee] WARN: path does not exist: {root}")
        return samples
    pat = re.compile(r"^([A-Z]{2})_([a-z]+)\d+$")
    for wav in root.rglob("*.wav"):
        m = pat.match(wav.stem)
        if not m:
            continue
        speaker = m.group(1)
        emo_part = m.group(2)
        if speaker not in SAVEE_SPEAKER_MAP:
            continue
        label = None
        for prefix, lbl in SAVEE_EMOTION_PREFIXES:
            if emo_part.startswith(prefix):
                label = lbl
                break
        if label is None:
            continue
        samples.append(AudioSample(
            path=str(wav),
            label=label,
            label_name=EMOTIONS[label],
            actor_id=SAVEE_SPEAKER_MAP[speaker],
            dataset="savee",
            speaker_gender="M",
        ))
    return samples


# ============================================================
# Combined loader
# ============================================================
def load_all(audio_root: str | Path) -> List[AudioSample]:
    """audio_root should be the parent dir containing RAVDESS/, TESS/, SAVEE/."""
    root = Path(audio_root)
    return (
        load_ravdess(root / "RAVDESS")
        + load_tess(root / "TESS")
        + load_savee(root / "SAVEE")
    )


# ============================================================
# Stratified random split (Phase 2C - follows Pepino 2021,
# Chen 2022, Morais 2022 evaluation protocol)
# ============================================================
VAL_FRAC = 0.10
TEST_FRAC = 0.10
SPLIT_SEED = 42

# Kept for backward compatibility with data_audit.py output
VAL_ACTORS: set = set()
TEST_ACTORS: set = set()


def split_samples(
    samples: List[AudioSample],
    val_frac: float = VAL_FRAC,
    test_frac: float = TEST_FRAC,
    seed: int = SPLIT_SEED,
) -> Tuple[List[AudioSample], List[AudioSample], List[AudioSample]]:
    """Stratified random split: each emotion class is split independently
    so train/val/test maintain identical class distributions."""
    rng = random.Random(seed)
    by_label: dict = defaultdict(list)
    for s in samples:
        by_label[s.label].append(s)

    train, val, test = [], [], []
    for label, group in by_label.items():
        group = list(group)
        rng.shuffle(group)
        n = len(group)
        n_test = int(round(n * test_frac))
        n_val = int(round(n * val_frac))
        test.extend(group[:n_test])
        val.extend(group[n_test:n_test + n_val])
        train.extend(group[n_test + n_val:])

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test