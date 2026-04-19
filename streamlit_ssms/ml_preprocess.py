"""
FER-style preprocessing for the Colab emotion model — matches backend/app/ml/preprocess.py
(48×48 grayscale, NHWC) so the same .keras file works in Streamlit and Flask.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image


def pil_rgb_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def emotion_input_tensor_from_rgb(rgb: Image.Image, size: int = 48) -> np.ndarray:
    gray = rgb.convert("L").resize((size, size))
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    return arr.reshape(1, size, size, 1)
