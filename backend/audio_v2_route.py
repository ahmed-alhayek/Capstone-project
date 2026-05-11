"""
 audio analysis route.

Adds POST /api/analyze-audio-v2 that uses the HuBERT model.
Existing /api/analyze-audio (Phase 1 CNN+LSTM) remains as a fallback .
"""

import sys
import tempfile
import os
import traceback
from pathlib import Path

from flask import Blueprint, request, jsonify

# Add audio_model/v2_transformers to import path
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
V2_DIR = PROJECT_ROOT / "audio_model" / "v2_transformers"
sys.path.insert(0, str(V2_DIR))

# Import lazily inside the route so app.py boots fast even before
# the model is needed. We do a one-time check here though:
try:
    from predict_v2 import predict_emotion as _predict_emotion_v2
    _IMPORT_ERROR = None
except Exception as e:
    _predict_emotion_v2 = None
    _IMPORT_ERROR = str(e)


audio_v2_bp = Blueprint("audio_v2", __name__)


@audio_v2_bp.route("/api/analyze-audio-v2", methods=["POST"])
def analyze_audio_v2():
    if _predict_emotion_v2 is None:
        return jsonify({
            "error": "predict_v2 not available",
            "detail": _IMPORT_ERROR,
        }), 500

    if "audio" not in request.files:
        return jsonify({"error": "no audio file in request"}), 400

    f = request.files["audio"]
    suffix = Path(f.filename or "upload.wav").suffix or ".wav"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name

        result = _predict_emotion_v2(tmp_path)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "inference failed", "detail": str(e)}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@audio_v2_bp.route("/api/analyze-audio-v2/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok" if _predict_emotion_v2 is not None else "import_error",
        "import_error": _IMPORT_ERROR,
        "v2_path": str(V2_DIR),
    }), 200