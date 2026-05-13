"""
face_model/predict_face.py

Facial emotion recognition using fine-tuned EfficientNetV2S (FER+).
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Union

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

CLASSES = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear', 'contempt']
NUM_CLASSES = len(CLASSES)
IMG_SIZE = 224

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = PROJECT_ROOT / "face_model" / "weights" / "effnet_ferplus_best.pth"

_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE), interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_DEVICE = None
_MODEL = None
_FACE_CASCADE = None


def _ensure_loaded():
    global _DEVICE, _MODEL, _FACE_CASCADE
    if _MODEL is not None:
        return

    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Face model weights not found at {WEIGHTS_PATH}\n"
            "Place effnet_ferplus_best.pth in face_model/weights/"
        )

    _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[predict_face] Loading EfficientNetV2S on {_DEVICE}...")

    model = models.efficientnet_v2_s(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.35),
        nn.Linear(in_features, NUM_CLASSES),
    )
    state = torch.load(str(WEIGHTS_PATH), map_location=_DEVICE)
    model.load_state_dict(state)
    model.to(_DEVICE)
    model.eval()
    _MODEL = model

    _FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    print("[predict_face] Ready.")


def _to_pil(image: Union[str, Path, bytes, np.ndarray, Image.Image]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (str, Path)):
        return Image.open(image).convert("RGB")
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image)).convert("RGB")
    if isinstance(image, np.ndarray):
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    raise TypeError(f"Unsupported image type: {type(image)}")


def predict_face_emotion(image: Union[str, Path, bytes, np.ndarray, Image.Image]) -> dict:
    """
    Detect the largest face in the image and return 8-class emotion probabilities.

    Returns:
        {
            "emotions": {"neutral": 0.1, "happiness": 0.6, ...},
            "dominant_emotion": "happiness",
            "confidence": 0.62,
            "face_detected": True,
            "model": "efficientnet_v2s_ferplus"
        }
    If no face is detected, returns face_detected=False with zero probabilities.
    """
    _ensure_loaded()

    pil_img = _to_pil(image)
    # Upscale small images so the Haar cascade can detect faces reliably
    w, h = pil_img.size
    if max(w, h) < 200:
        scale = 200 / max(w, h)
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))

    zero_emotions = {cls: 0.0 for cls in CLASSES}
    if len(faces) == 0:
        return {
            "emotions": zero_emotions,
            "dominant_emotion": "neutral",
            "confidence": 0.0,
            "face_detected": False,
            "model": "efficientnet_v2s_ferplus",
        }

    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
    face_bgr = bgr[y:y + h, x:x + w]
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_pil = Image.fromarray(face_rgb)

    tensor = _transform(face_pil).unsqueeze(0).to(_DEVICE)

    with torch.no_grad():
        logits = _MODEL(tensor)
        probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()

    emotions = {cls: round(float(probs[i]), 4) for i, cls in enumerate(CLASSES)}
    dominant = CLASSES[int(probs.argmax())]
    confidence = round(float(probs.max()), 4)

    return {
        "emotions": emotions,
        "dominant_emotion": dominant,
        "confidence": confidence,
        "face_detected": True,
        "model": "efficientnet_v2s_ferplus",
    }
