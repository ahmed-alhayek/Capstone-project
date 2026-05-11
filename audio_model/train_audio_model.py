"""
Audio Emotion Model with Data Augmentation
"""

import numpy as np
import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import pickle
from tqdm import tqdm

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
CONFIG = {
    "batch_size"    : 32,
    "epochs"        : 80,        # more epochs for small dataset
    "learning_rate" : 0.0005,    # slightly lower learning rate
    "dropout"       : 0.4,
    "output_dir"    : "saved_audio_model",
}

NUM_CLASSES = 8
EMOTION_LABELS = [
    'neutral', 'calm', 'happy', 'sad',
    'angry', 'fearful', 'disgust', 'surprised'
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("\nLoading features...")
X_train = np.load('X_train.npy')
X_val   = np.load('X_val.npy')
X_test  = np.load('X_test.npy')
y_train = np.load('y_train.npy')
y_val   = np.load('y_val.npy')
y_test  = np.load('y_test.npy')

print(f"  Train: {X_train.shape[0]} | Val: {X_val.shape[0]} | Test: {X_test.shape[0]}")

# ── DATA AUGMENTATION ─────────────────────────────────────────────────────────
def augment_features(X, y, augment_factor=3):
    """
    Creates artificial new samples by adding small random noise to existing ones.
    
    
    """
    X_augmented = [X]
    y_augmented = [y]

    for _ in range(augment_factor):
        # Add small Gaussian noise (mean=0, std=0.05)
        noise = np.random.normal(0, 0.05, X.shape)
        X_noisy = X + noise
        X_augmented.append(X_noisy)
        y_augmented.append(y)

    X_aug = np.vstack(X_augmented)
    y_aug = np.concatenate(y_augmented)

    # Shuffle the augmented data
    idx = np.random.permutation(len(X_aug))
    return X_aug[idx], y_aug[idx]

print("\nApplying data augmentation...")
X_train, y_train = augment_features(X_train, y_train, augment_factor=3)
print(f"  Train samples after augmentation: {len(X_train)}")

# ── NORMALIZE ─────────────────────────────────────────────────────────────────
scaler  = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val   = scaler.transform(X_val)
X_test  = scaler.transform(X_test)

os.makedirs(CONFIG["output_dir"], exist_ok=True)
with open(os.path.join(CONFIG["output_dir"], 'scaler.pkl'), 'wb') as f:
    pickle.dump(scaler, f)

# Reshape for CNN: (samples, 1, features)
X_train = X_train[:, np.newaxis, :]
X_val   = X_val[:,   np.newaxis, :]
X_test  = X_test[:,  np.newaxis, :]

# ── DATASET ───────────────────────────────────────────────────────────────────
class AudioDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels   = torch.tensor(labels,   dtype=torch.long)
    def __len__(self):
        return len(self.features)
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

train_loader = DataLoader(AudioDataset(X_train, y_train), batch_size=CONFIG["batch_size"], shuffle=True)
val_loader   = DataLoader(AudioDataset(X_val,   y_val),   batch_size=CONFIG["batch_size"], shuffle=False)
test_loader  = DataLoader(AudioDataset(X_test,  y_test),  batch_size=CONFIG["batch_size"], shuffle=False)

# ── IMPROVED MODEL ────────────────────────────────────────────────────────────
class AudioEmotionModel(nn.Module):
    
    def __init__(self, input_size=220, num_classes=NUM_CLASSES, dropout=CONFIG["dropout"]):
        super(AudioEmotionModel, self).__init__()

        # CNN Block 1
        self.cnn1 = nn.Sequential(
            nn.Conv1d(1,   64,  kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64,  64,  kernel_size=3, padding=1),
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

        # LSTM
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
        x = self.cnn1(x)         # (batch, 64,  110)
        x = self.cnn2(x)         # (batch, 128,  55)
        x = self.cnn3(x)         # (batch, 256,  55)
        x = x.permute(0, 2, 1)  # (batch, 55,  256)
        x, _ = self.lstm(x)      # (batch, 55,  256)
        x = x[:, -1, :]          # (batch, 256)
        x = self.classifier(x)   # (batch,   8)
        return x

# ── TRAINING SETUP ────────────────────────────────────────────────────────────
model     = AudioEmotionModel().to(device)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)  # label smoothing reduces overconfidence
optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["learning_rate"], weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=CONFIG["epochs"]
)  # cosine scheduler smoothly reduces LR over all epochs

total_params = sum(p.numel() for p in model.parameters())
print(f"\nModel parameters: {total_params:,}")

# ── TRAINING FUNCTIONS ────────────────────────────────────────────────────────
def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for features, labels in loader:
        features, labels = features.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(features)
        loss    = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # prevent exploding gradients
        optimizer.step()
        total_loss += loss.item()
        correct    += (outputs.argmax(1) == labels).sum().item()
        total      += labels.size(0)
    return total_loss / len(loader), correct / total

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for features, labels in loader:
            features, labels = features.to(device), labels.to(device)
            outputs     = model(features)
            loss        = criterion(outputs, labels)
            total_loss += loss.item()
            preds       = outputs.argmax(1)
            correct    += (preds == labels).sum().item()
            total      += labels.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return total_loss / len(loader), correct / total, all_preds, all_labels

# ── TRAINING LOOP ─────────────────────────────────────────────────────────────
print(f"\nTraining for {CONFIG['epochs']} epochs...")
best_val_acc = 0
history      = []

for epoch in range(CONFIG["epochs"]):
    train_loss, train_acc       = train_one_epoch(model, train_loader, optimizer, criterion, device)
    val_loss, val_acc, _, _     = evaluate(model, val_loader, criterion, device)
    scheduler.step()

    print(f"Epoch {epoch+1:02d}/{CONFIG['epochs']} | "
          f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | "
          f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f}")

    history.append({
        "epoch": epoch+1, "train_loss": round(train_loss,4),
        "train_acc": round(train_acc,4), "val_loss": round(val_loss,4),
        "val_acc": round(val_acc,4)
    })

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), os.path.join(CONFIG["output_dir"], 'best_model.pt'))
        print(f"   Best model saved! (Val Acc: {best_val_acc:.3f})")

# ── FINAL RESULTS ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"TRAINING COMPLETE | Best Val Accuracy: {best_val_acc:.3f}")
print(f"{'='*60}")

model.load_state_dict(torch.load(os.path.join(CONFIG["output_dir"], 'best_model.pt')))
_, test_acc, test_preds, test_labels = evaluate(model, test_loader, criterion, device)
print(f"Test Accuracy: {test_acc:.3f}")
print("\nPer-Emotion Report:")
print(classification_report(test_labels, test_preds, target_names=EMOTION_LABELS))

with open("audio_training_history.json", "w") as f:
    json.dump(history, f, indent=2)

with open(os.path.join(CONFIG["output_dir"], 'model_config.json'), "w") as f:
    json.dump({"input_size": 220, "num_classes": NUM_CLASSES,
               "emotions": EMOTION_LABELS, "config": CONFIG}, f, indent=2)

print(f"\n Model saved to '{CONFIG['output_dir']}/'")
print(f" History saved to 'audio_training_history.json'")