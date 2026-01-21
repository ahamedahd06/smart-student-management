"""Utilities for emotion detection and (future) face recognition."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from tensorflow.keras.models import load_model

EMOTION_LABELS = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral",
]


def load_emotion_model(model_path: Path):
    """Load a Keras emotion model from disk."""
    return load_model(model_path)


def detect_primary_face(gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect the largest face in a grayscale image."""
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) == 0:
        return None
    return max(faces, key=lambda box: box[2] * box[3])


def preprocess_face(face_gray: np.ndarray, target_size: Tuple[int, int] = (48, 48)) -> np.ndarray:
    """Resize and normalize a face image for model inference."""
    resized = cv2.resize(face_gray, target_size, interpolation=cv2.INTER_AREA)
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=(0, -1))


def predict_emotion(
    model,
    face_tensor: np.ndarray,
) -> Tuple[str, float, Dict[str, float]]:
    """Predict emotion label, confidence, and full probability map."""
    preds = model.predict(face_tensor, verbose=0)[0]
    max_idx = int(np.argmax(preds))
    label = EMOTION_LABELS[max_idx]
    confidence = float(preds[max_idx])
    prob_map = {label_name: float(pred) for label_name, pred in zip(EMOTION_LABELS, preds)}
    return label, confidence, prob_map


def identify_student_from_face(_image: np.ndarray) -> Optional[str]:
    """Phase 2 stub for face recognition (future enhancement)."""
    return None
