"""
backend/face_route.py

Facial emotion analysis endpoint using EfficientNetV2S (FER+).
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path

from flask import Blueprint, request, jsonify

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from face_model.predict_face import predict_face_emotion as _predict_face
    _IMPORT_ERROR = None
except Exception as e:
    _predict_face = None
    _IMPORT_ERROR = str(e)

face_bp = Blueprint("face", __name__)


@face_bp.route("/api/analyze-face", methods=["POST"])
def analyze_face():
    if _predict_face is None:
        return jsonify({"error": "face model not available", "detail": _IMPORT_ERROR}), 500

    if "image" not in request.files:
        return jsonify({"error": "no image file in request"}), 400

    f = request.files["image"]
    suffix = Path(f.filename or "upload.jpg").suffix or ".jpg"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name

        result = _predict_face(tmp_path)
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


@face_bp.route("/api/analyze-face/health", methods=["GET"])
def face_health():
    return jsonify({
        "status": "ok" if _predict_face is not None else "import_error",
        "import_error": _IMPORT_ERROR,
        "model": "efficientnet_v2s_ferplus",
        "weights_path": str(PROJECT_ROOT / "face_model" / "weights" / "effnet_ferplus_best.pth"),
    }), 200
