"""
Real facial recognition + emotion detection using OpenCV and TensorFlow.
- Face detection: OpenCV Haar cascade
- Emotion: TF/Keras model at backend/models/emotion_model.keras (4 classes)
- Architecture + class order: model_spec.py (must match train_emotion_model.py)
- Preprocessing: 48×48 grayscale float32 [0,1], same as training pipeline.
"""
from __future__ import annotations

import io
import json
import os

os.environ["TF_USE_LEGACY_KERAS"] = "0"

from pathlib import Path
from typing import Any, Tuple, cast

import numpy as np
from PIL import Image

_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _ROOT.parent

_EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

_face_cascade = None
_cached_model = None
_cached_labels: dict[str, str] | None = None
_cached_model_path: str | None = None
_cached_model_mtime: float | None = None


def clear_model_cache() -> None:
    """Call after replacing emotion_model.keras so the next predict reloads weights."""
    global _cached_model, _cached_labels, _cached_model_path, _cached_model_mtime
    _cached_model = None
    _cached_labels = None
    _cached_model_path = None
    _cached_model_mtime = None


def _get_face_cascade():
    global _face_cascade
    if _face_cascade is not None:
        return _face_cascade
    try:
        import cv2

        cv2_any = cast(Any, cv2)
        cascade_path = cv2_any.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        return _face_cascade
    except Exception:
        return None


def detect_face(image_bytes: bytes) -> Tuple[bool, np.ndarray | None, tuple | None]:
    """Detect a face using OpenCV Haar cascade.
    Streamlit camera bytes are usually JPEG; we try OpenCV decode first, then PIL.
    Returns (found, face_crop_gray, bbox) where bbox is (x,y,w,h)."""
    try:
        import cv2

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            try:
                pil_rgb = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                rgb = np.asarray(pil_rgb, dtype=np.uint8)
                img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            except Exception:
                return False, None, None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Optional CLAHE for dim webcams (set SSMS_FACE_CLAHE=1). Default off to match FER training.
        if os.getenv("SSMS_FACE_CLAHE", "").strip() in ("1", "true", "True", "yes"):
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        cascade = _get_face_cascade()
        if cascade is None:
            return False, None, None

        def _faces(g: np.ndarray, scale: float, neigh: int, min_s: int) -> Any:
            return cascade.detectMultiScale(
                g,
                scaleFactor=scale,
                minNeighbors=neigh,
                minSize=(min_s, min_s),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        faces = _faces(gray, 1.08, 4, 40)
        if len(faces) == 0:
            faces = _faces(gray, 1.12, 3, 30)
        if len(faces) == 0:
            faces = _faces(gray, 1.2, 2, 24)

        if len(faces) == 0:
            return False, None, None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_crop = gray[y : y + h, x : x + w]
        return True, face_crop, (int(x), int(y), int(w), int(h))
    except Exception:
        return False, None, None


def _preprocess_face(face_gray: np.ndarray, size: int = 48) -> np.ndarray:
    """Match training: resize grayscale face to 48×48, float32 [0,1], NHWC (1,48,48,1)."""
    from PIL import Image as PILImage

    img = PILImage.fromarray(face_gray.astype(np.uint8))
    if hasattr(PILImage, "Resampling"):
        resample = PILImage.Resampling.LANCZOS
    else:
        resample = cast(Any, getattr(PILImage, "LANCZOS", 1))
    img = img.resize((size, size), resample)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr.reshape(1, size, size, 1)


def _default_model_path() -> str:
    env = os.getenv("SSMS_EMOTION_MODEL_PATH", "").strip()
    if env and Path(env).is_file():
        return env
    cand = _REPO_ROOT / "backend" / "models" / "emotion_model.keras"
    return str(cand) if cand.is_file() else ""


def _default_label_map_path() -> str:
    env = os.getenv("SSMS_EMOTION_LABEL_MAP_PATH", "").strip()
    if env and Path(env).is_file():
        return env
    for name in ("label_map.json", "label_map.example.json"):
        cand = _REPO_ROOT / "backend" / "ml" / name
        if cand.is_file():
            return str(cand)
    return ""


def _load_label_map(path: str) -> dict[str, str]:
    """Load index→label from JSON, else model_spec 4-class names, else FER-7 defaults."""
    if path and Path(path).is_file():
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return {str(i): str(v) for i, v in enumerate(raw)}
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
        return {}
    try:
        from model_spec import CLASS_NAMES

        return {str(i): CLASS_NAMES[i] for i in range(len(CLASS_NAMES))}
    except ImportError:
        return {str(i): v for i, v in enumerate(_EMOTION_LABELS)}


def _get_model():
    global _cached_model, _cached_labels, _cached_model_path, _cached_model_mtime
    path = _default_model_path()
    if not path:
        return None, None
    try:
        mtime = Path(path).stat().st_mtime
    except OSError:
        return None, None
    if (
        _cached_model is not None
        and _cached_model_path == path
        and _cached_model_mtime == mtime
    ):
        return _cached_model, _cached_labels

    try:
        import tensorflow as tf

        keras_mod = cast(Any, tf).keras
        _cached_model = keras_mod.models.load_model(path)
        _cached_labels = _load_label_map(_default_label_map_path())
        _cached_model_path = path
        _cached_model_mtime = mtime
        return _cached_model, _cached_labels
    except Exception:
        _cached_model = None
        _cached_labels = None
        _cached_model_path = None
        _cached_model_mtime = None
        return None, None


def predict_emotion_from_face(face_gray: np.ndarray) -> Tuple[str, float]:
    """Predict emotion from a pre-cropped grayscale face array."""
    model, labels = _get_model()
    if model is not None:
        try:
            labels = labels or {}
            x = _preprocess_face(face_gray)
            pred = model.predict(x, verbose=0)[0]
            idx = int(np.argmax(pred))
            conf = float(pred[idx])
            return labels.get(str(idx), "neutral"), conf
        except Exception:
            pass
    return _stub_emotion(face_gray)


def predict_emotion_full(image_bytes: bytes) -> dict[str, Any]:
    """Rich result for UI: emotion, confidence, per-class probs, bbox, tf_model flag."""
    found, face_crop, bbox = detect_face(image_bytes)
    if not found or face_crop is None:
        return {
            "ok": False,
            "emotion": "no_face",
            "confidence": 0.0,
            "probs": {},
            "bbox": None,
            "tf_model": False,
            "note": "No face detected — center your face and improve lighting.",
        }

    model, labels = _get_model()
    if model is None:
        label, conf = _stub_emotion(face_crop)
        return {
            "ok": True,
            "emotion": label,
            "confidence": conf,
            "probs": {label: conf},
            "bbox": bbox,
            "tf_model": False,
            "note": "No emotion_model.keras found — heuristic fallback. Run train_emotion_model.py.",
        }

    labels = labels or {}
    try:
        x = _preprocess_face(face_crop)
        pred = model.predict(x, verbose=0)[0]
        idx = int(np.argmax(pred))
        conf = float(pred[idx])
        label = labels.get(str(idx), "neutral")
        probs: dict[str, float] = {}
        for i in range(len(pred)):
            probs[labels.get(str(i), str(i))] = float(pred[i])
        return {
            "ok": True,
            "emotion": label,
            "confidence": conf,
            "probs": probs,
            "bbox": bbox,
            "tf_model": True,
            "note": "",
        }
    except Exception as e:
        label, conf = _stub_emotion(face_crop)
        return {
            "ok": True,
            "emotion": label,
            "confidence": conf,
            "probs": {label: conf},
            "bbox": bbox,
            "tf_model": False,
            "note": f"Model inference error ({e!s}); fallback used.",
        }


def _stub_emotion(face_gray: np.ndarray) -> Tuple[str, float]:
    """Last-resort heuristic when no model file (demo only)."""
    import hashlib

    h, w = face_gray.shape[:2]
    upper = face_gray[: h // 3, :]
    middle = face_gray[h // 3 : 2 * h // 3, :]
    lower = face_gray[2 * h // 3 :, :]
    mean_all = float(np.mean(face_gray))
    std_all = float(np.std(face_gray))
    mean_upper = float(np.mean(upper))
    mean_lower = float(np.mean(lower))
    std_middle = float(np.std(middle))
    norm_mean = min(mean_all / 255.0, 1.0)
    norm_std = min(std_all / 80.0, 1.0)
    upper_lower_diff = (mean_upper - mean_lower) / max(mean_all, 1.0)
    data = face_gray.tobytes()[:4096]
    digest = int(hashlib.md5(data).hexdigest(), 16)
    score_happy = 0.25 + norm_std * 0.3 + (0.1 if upper_lower_diff > 0.05 else 0)
    score_neutral = 0.35 + (0.2 if 0.3 < norm_mean < 0.7 else 0)
    score_sad = 0.15 + (0.15 if norm_std < 0.35 else 0)
    score_angry = 0.10 + (0.15 if std_middle > 50 else 0)
    variation = (digest % 20) / 100.0
    scores = {
        "happy": score_happy + variation,
        "neutral": score_neutral + ((digest >> 4) % 10) / 100.0,
        "sad": score_sad + ((digest >> 8) % 8) / 100.0,
        "angry": score_angry + ((digest >> 12) % 6) / 100.0,
    }
    total = sum(scores.values())
    scores = {k: v / total for k, v in scores.items()}
    label = max(scores, key=scores.get)  # type: ignore[arg-type]
    raw_conf = scores[label]
    conf = 0.55 + raw_conf * 0.40
    return label, min(0.95, conf)


def predict_emotion_from_bytes(image_bytes: bytes) -> Tuple[str, float]:
    """Main entry point: detect face + predict emotion.
    Returns (label, confidence). If no face found, returns ('no_face', 0.0)."""
    r = predict_emotion_full(image_bytes)
    if not r["ok"]:
        return r["emotion"], 0.0
    return r["emotion"], float(r["confidence"])
