
"""

Loads the trained CNN+LSTM audio model and predicts
emotions from a WAV audio file.


"""

import os
import numpy as np
import librosa
import pickle
import torch
import torch.nn as nn
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
AUDIO_MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_audio_model')
SCALER_PATH     = os.path.join(AUDIO_MODEL_DIR, 'scaler.pkl')
LABELS_PATH     = os.path.join(os.path.dirname(__file__), 'emotion_labels.npy')

N_MFCC      = 80
N_CHROMA    = 12
N_MEL       = 128
SAMPLE_RATE = 22050
DURATION    = 3
N_FEATURES  = N_MFCC + N_CHROMA + N_MEL  # = 220

NUM_CLASSES = 8
DROPOUT     = 0.4


# ── MODEL ARCHITECTURE (exactly matches train_audio_model.py) ─────────────────

class AudioEmotionModel(nn.Module):
    """
    CNN + Bidirectional LSTM model.
    This architecture must exactly match train_audio_model.py.
    """

    def __init__(self, input_size=220, num_classes=NUM_CLASSES, dropout=DROPOUT):
        super(AudioEmotionModel, self).__init__()

        # CNN Block 1
        self.cnn1 = nn.Sequential(
            nn.Conv1d(1,  64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(dropout)
        )

        # CNN Block 2
        self.cnn2 = nn.Sequential(
            nn.Conv1d(64,  128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Conv1d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(dropout)
        )

        # CNN Block 3
        self.cnn3 = nn.Sequential(
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            dropout=dropout,
            bidirectional=True
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = self.cnn1(x)
        x = self.cnn2(x)
        x = self.cnn3(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm(x)
        x = x[:, -1, :]
        return self.classifier(x)


# ── LOAD MODEL ────────────────────────────────────────────────────────────────

def _load_model():
    """Loads the trained audio model, scaler, and emotion labels."""

    emotion_labels = list(np.load(LABELS_PATH, allow_pickle=True))
    num_classes    = len(emotion_labels)

    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = AudioEmotionModel(input_size=N_FEATURES, num_classes=num_classes)
    model.load_state_dict(
        torch.load(
            os.path.join(AUDIO_MODEL_DIR, 'best_model.pt'),
            map_location=device
        )
    )
    model.to(device)
    model.eval()

    return model, scaler, emotion_labels, device


# Load once when module is imported
_model, _scaler, _emotion_labels, _device = _load_model()
print("✅ Audio emotion model loaded!")


# ── FEATURE EXTRACTION ────────────────────────────────────────────────────────

def _extract_features(audio_path: str) -> np.ndarray:
    """
    Extracts MFCC + Chroma + Mel Spectrogram features from a WAV file.
    Must match exactly what was done in preprocess_audio.py.
    """
    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, duration=DURATION)

    expected_length = SAMPLE_RATE * DURATION
    if len(y) < expected_length:
        y = np.pad(y, (0, expected_length - len(y)))

    mfcc   = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=N_CHROMA)
    mel    = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=N_MEL)

    features = np.concatenate([
        np.mean(mfcc,   axis=1),
        np.mean(chroma, axis=1),
        np.mean(mel,    axis=1)
    ])

    return features


# ── PREDICTION FUNCTION ───────────────────────────────────────────────────────

def predict_audio_emotions(audio_path: str) -> dict:
    """
    Predicts emotions from a WAV audio file.

    Parameters:
    - audio_path: full path to the WAV file

    Returns:
    - dict of emotion probabilities e.g:
      { 'neutral': 0.65, 'sad': 0.20, 'fearful': 0.10, ... }
    """
    features        = _extract_features(audio_path)
    features_scaled = _scaler.transform(features.reshape(1, -1))

    # Reshape to (batch=1, channels=1, features=220) to match training shape
    tensor = torch.FloatTensor(
        features_scaled[:, np.newaxis, :]
    ).to(_device)

    with torch.no_grad():
        logits = _model(tensor)
        probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

    emotion_probs = {
        label: round(float(prob), 4)
        for label, prob in zip(_emotion_labels, probs)
    }

    return emotion_probs


# ── ONLY RUNS WHEN EXECUTED DIRECTLY ─────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict_audio.py <path_to_wav_file>")
        sys.exit(1)

    audio_path = sys.argv[1]
    print(f"\n🎤 Analyzing: {audio_path}")
    emotions = predict_audio_emotions(audio_path)

    print("\n🎯 Detected Audio Emotions:")
    for emotion, prob in sorted(emotions.items(), key=lambda x: -x[1]):
        bar = "█" * int(prob * 30)
        print(f"   {emotion:<12} {bar} {prob:.1%}")