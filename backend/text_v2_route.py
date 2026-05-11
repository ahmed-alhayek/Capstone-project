"""
backend/text_v2_route.py

Text emotion analysis endpoint using fine-tuned RoBERTa (Option C).
Mirrors the audio_v2_route pattern: lazy model load, /v2 endpoint, health check.
"""

import sys
import traceback
import importlib.util
from pathlib import Path
from flask import Blueprint, request, jsonify

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEXT_PREDICT_PATH = PROJECT_ROOT / "text_model" / "finetune" / "predict_v2.py"


# colliding with audio_model/v2_transformers/predict_v2.py which Flask also loads.
# Reuse if already loaded by test_text_model.py (avoid double-loading into VRAM).
_MODULE_NAME = "text_predict_v2"
if _MODULE_NAME in sys.modules:
    text_predict = sys.modules[_MODULE_NAME]
else:
    _spec = importlib.util.spec_from_file_location(_MODULE_NAME, TEXT_PREDICT_PATH)
    text_predict = importlib.util.module_from_spec(_spec)
    sys.modules[_MODULE_NAME] = text_predict
    _spec.loader.exec_module(text_predict)

text_v2_bp = Blueprint("text_v2", __name__, url_prefix="/api")

_model_loaded = False


def _ensure_model_loaded():
    """Lazy load the model on first request to avoid blocking Flask startup."""
    global _model_loaded
    if not _model_loaded:
        print("[text_v2_route] Loading fine-tuned RoBERTa (lazy, on first request)...")
        text_predict.load_model()
        _model_loaded = True
        print("[text_v2_route] RoBERTa ready.")


@text_v2_bp.route("/analyze-text-v2", methods=["POST"])
def analyze_text_v2():
    try:
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "Field 'text' is required and must be non-empty."}), 400
        if len(text) > 5000:
            return jsonify({"error": "Text exceeds 5000 character limit."}), 400

        _ensure_model_loaded()
        result = text_predict.predict(text, threshold=0.20, top_k=5)

        detected = [
            {"emotion": e, "probability": round(p, 4)}
            for e, p in result["above_threshold"]
        ]
        top_k = [
            {"emotion": e, "probability": round(p, 4)}
            for e, p in result["top_k"]
        ]

        return jsonify({
            "text": text,
            "detected_emotions": detected,
            "top_emotions": top_k,
            "model_version": "roberta_goemotions_finetuned",
        })

    except Exception as exc:
        print(f"[text_v2_route] Error: {exc}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error during text analysis."}), 500


@text_v2_bp.route("/analyze-text-v2/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": "roberta-base fine-tuned on GoEmotions",
        "loaded": _model_loaded,
    })