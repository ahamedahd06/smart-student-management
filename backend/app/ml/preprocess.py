"""Image preprocessing for emotion CNN (FER-style grayscale 48x48)."""

from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image


def pil_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def emotion_input_tensor_from_rgb(rgb: Image.Image, size: int = 48) -> np.ndarray:
    gray = rgb.convert("L").resize((size, size))
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    # NHWC single channel — matches typical Keras Conv2D input
    return arr.reshape(1, size, size, 1)


def crop_face_rgb(rgb: Image.Image, location: Tuple[int, int, int, int] | None) -> Image.Image:
    """location is (top, right, bottom, left) as from face_recognition."""
    if not location:
        return rgb
    top, right, bottom, left = location
    return rgb.crop((left, top, right, bottom))
