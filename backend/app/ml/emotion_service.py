from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
from flask import current_app
from PIL import Image

from app.ml.preprocess import emotion_input_tensor_from_rgb

_model = None
_label_map: dict[str, str] | None = None
_load_attempted = False


class EmotionModelError(Exception):
    pass


def _default_label_map() -> dict[str, str]:
    # Documented contract: indices 0..3 map to these labels after Colab export
    return {"0": "angry", "1": "happy", "2": "neutral", "3": "sad"}


def load_model() -> None:
    global _model, _label_map, _load_attempted
    _load_attempted = True
    path = current_app.config.get("EMOTION_MODEL_PATH", "")
    map_path = current_app.config.get("EMOTION_LABEL_MAP_PATH", "")
    if not path or not os.path.isfile(path):
        _model = None
        _label_map = None
        return
    try:
        # Some Windows environments set this globally; it breaks model loading unless tf_keras is installed.
        if os.environ.get("TF_USE_LEGACY_KERAS", "").lower() in {"1", "true", "yes"}:
            os.environ["TF_USE_LEGACY_KERAS"] = "0"
        import tensorflow as tf

        _model = tf.keras.models.load_model(path)
        if map_path and os.path.isfile(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            _label_map = {str(k): str(v) for k, v in raw.items()}
        else:
            _label_map = _default_label_map()
    except Exception:
        _model = None
        _label_map = None


def model_ready() -> bool:
    global _load_attempted
    if not _load_attempted:
        load_model()
    return _model is not None


def predict_emotion_rgb(face_crop: Image.Image) -> tuple[str, float]:
    if not model_ready():
        raise EmotionModelError(
            "Emotion model not loaded. Set EMOTION_MODEL_PATH to a Keras model file "
            "exported from Colab (.keras or .h5) and optionally EMOTION_LABEL_MAP_PATH."
        )
    x = emotion_input_tensor_from_rgb(face_crop)
    preds = _model.predict(x, verbose=0)[0]
    idx = int(np.argmax(preds))
    conf = float(preds[idx])
    lm = _label_map or _default_label_map()
    label = lm.get(str(idx), "neutral")
    return label, conf


def label_order_doc() -> dict[str, Any]:
    """Human-readable contract for viva / Colab alignment."""
    return {
        "input_shape": {"batch": 1, "height": 48, "width": 48, "channels": 1},
        "preprocess": "Grayscale, resize 48x48, float32 /255.0, shape (1,48,48,1)",
        "default_label_indices": _default_label_map(),
        "note": "Training in Colab should export label_map.json matching your final dense layer order.",
    }
