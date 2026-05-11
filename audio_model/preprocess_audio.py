"""
STEP 4 — Audio Data Preprocessing (RAVDESS Dataset)
AI Mental Health Companion | Capstone Project
=====================================================
This script loads all .wav files from the RAVDESS dataset,
extracts audio features (MFCC, Chroma, Mel) using Librosa,
and saves them ready for model training.

📁 File location: mental_health_companion/audio_model/step4_preprocess_audio.py
📋 Requires: RAVDESS/ folder with Actor_01 to Actor_24
"""

import os
import numpy as np
import librosa
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
RAVDESS_DIR = "RAVDESS"       # folder containing Actor_01 ... Actor_24
SAMPLE_RATE = 22050           # standard audio sample rate
DURATION    = 3               # seconds to load per file (RAVDESS files ~3.5s)
N_MFCC      = 40              # number of MFCC coefficients to extract

# ── EMOTION MAPPING ───────────────────────────────────────────────────────────
# RAVDESS encodes emotion in the 3rd part of the filename
# Example: 03-01-04-01-01-01-01.wav → emotion code = 04 = sad
EMOTION_MAP = {
    '01': 'neutral',
    '02': 'calm',
    '03': 'happy',
    '04': 'sad',
    '05': 'angry',
    '06': 'fearful',
    '07': 'disgust',
    '08': 'surprised'
}

# ── FEATURE EXTRACTION ────────────────────────────────────────────────────────
def extract_features(file_path, sample_rate=SAMPLE_RATE, duration=DURATION, n_mfcc=N_MFCC):
    """
    Extracts audio features from a .wav file using Librosa.
    
    We extract 3 types of features:
    
    1. MFCC (Mel Frequency Cepstral Coefficients)
       - Most important feature for speech/emotion recognition
       - Captures the shape of the vocal tract
       - 40 coefficients × mean+std = 80 values
    
    2. Chroma Features
       - Represents the energy of different pitch classes
       - Useful for detecting tonal qualities in speech
       - 12 values
    
    3. Mel Spectrogram
       - Frequency representation that matches human hearing
       - 128 values
    
    Total feature vector: 80 + 12 + 128 = 220 values per audio file
    """
    try:
        # Load audio file
        # duration=3 means we only use first 3 seconds
        # offset=0.5 means we skip the first 0.5 seconds (removes silence)
        audio, sr = librosa.load(file_path, sr=sample_rate, duration=duration, offset=0.5)

        # Pad if audio is shorter than expected
        expected_length = sample_rate * duration
        if len(audio) < expected_length:
            audio = np.pad(audio, (0, expected_length - len(audio)))

        features = []

        # 1. MFCC — 40 coefficients, take mean and std = 80 values
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
        features.extend(np.mean(mfcc, axis=1))   # mean of each coefficient
        features.extend(np.std(mfcc, axis=1))    # std of each coefficient

        # 2. Chroma — 12 pitch classes, take mean = 12 values
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        features.extend(np.mean(chroma, axis=1))

        # 3. Mel Spectrogram — 128 mel bands, take mean = 128 values
        mel = librosa.feature.melspectrogram(y=audio, sr=sr)
        features.extend(np.mean(mel, axis=1))

        return np.array(features)  # total: 220 features

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

# ── LOAD DATASET ──────────────────────────────────────────────────────────────
print("Loading RAVDESS dataset and extracting features...")
print("This may take a few minutes...\n")

all_features = []
all_labels   = []
all_emotions = []

# Walk through all Actor folders
actor_folders = sorted([
    f for f in os.listdir(RAVDESS_DIR)
    if os.path.isdir(os.path.join(RAVDESS_DIR, f))
])

print(f"Found {len(actor_folders)} actor folders\n")

for actor_folder in tqdm(actor_folders, desc="Processing actors"):
    actor_path = os.path.join(RAVDESS_DIR, actor_folder)

    for file_name in os.listdir(actor_path):
        if not file_name.endswith('.wav'):
            continue

        file_path = os.path.join(actor_path, file_name)

        # Extract emotion code from filename
        # Filename format: 03-01-04-01-01-01-01.wav
        # Parts split by '-': [modality, vocal_channel, emotion, intensity, statement, repetition, actor]
        parts = file_name.replace('.wav', '').split('-')
        if len(parts) < 3:
            continue

        emotion_code  = parts[2]  # 3rd part = emotion
        emotion_label = EMOTION_MAP.get(emotion_code)

        if emotion_label is None:
            continue

        # Extract features
        features = extract_features(file_path)
        if features is not None:
            all_features.append(features)
            all_labels.append(list(EMOTION_MAP.keys()).index(emotion_code))  # numeric label
            all_emotions.append(emotion_label)  # string label

# ── CONVERT TO NUMPY ARRAYS ───────────────────────────────────────────────────
X = np.array(all_features)
y = np.array(all_labels)

print(f"\n Feature extraction complete!")
print(f"   Total samples : {len(X)}")
print(f"   Feature size  : {X.shape[1]} per sample")
print(f"\nEmotion distribution:")
emotion_counts = pd.Series(all_emotions).value_counts()
for emotion, count in emotion_counts.items():
    print(f"   {emotion:<12}: {count} samples")

# ── TRAIN / VAL / TEST SPLIT ──────────────────────────────────────────────────
# 80% train | 10% val | 10% test
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

print(f"\nData split:")
print(f"   Train : {len(X_train)} samples")
print(f"   Val   : {len(X_val)} samples")
print(f"   Test  : {len(X_test)} samples")

# ── SAVE FEATURES ─────────────────────────────────────────────────────────────
np.save('X_train.npy', X_train)
np.save('X_val.npy',   X_val)
np.save('X_test.npy',  X_test)
np.save('y_train.npy', y_train)
np.save('y_val.npy',   y_val)
np.save('y_test.npy',  y_test)

# Save emotion labels mapping
np.save('emotion_labels.npy', np.array(list(EMOTION_MAP.values())))

print(f"\n Saved feature files:")
print(f"   X_train.npy | X_val.npy | X_test.npy")
print(f"   y_train.npy | y_val.npy | y_test.npy")
print(f"   emotion_labels.npy")
print(f"\nReady for model training! ")