from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image
from flask import current_app


def _try_face_recognition():
    try:
        import face_recognition  # type: ignore

        return face_recognition
    except Exception:
        return None


def rgb_array_from_bytes(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.asarray(img)


def encode_face(image_bytes: bytes) -> list[float] | None:
    fr = _try_face_recognition()
    if fr is None:
        return None
    rgb = rgb_array_from_bytes(image_bytes)
    encs = fr.face_encodings(rgb)
    if not encs:
        return None
    return encs[0].tolist()


def locate_largest_face(image_bytes: bytes) -> tuple[int, int, int, int] | None:
    fr = _try_face_recognition()
    if fr is None:
        return None
    rgb = rgb_array_from_bytes(image_bytes)
    locs = fr.face_locations(rgb)
    if not locs:
        return None
    # pick largest by area
    best = max(locs, key=lambda t: (t[2] - t[0]) * (t[3] - t[1]))
    return best  # top, right, bottom, left


def verify_same_person(image_bytes: bytes, known_encoding: list[float] | None) -> bool:
    if current_app.config.get("SKIP_FACE_VERIFICATION"):
        return True
    fr = _try_face_recognition()
    if fr is None or known_encoding is None:
        return False
    rgb = rgb_array_from_bytes(image_bytes)
    unknowns = fr.face_encodings(rgb)
    if not unknowns:
        return False
    dist = fr.face_distance([np.array(known_encoding)], unknowns[0])
    return bool(dist[0] <= 0.55)


def face_available() -> bool:
    return _try_face_recognition() is not None


def face_status() -> dict[str, Any]:
    return {
        "library_present": face_available(),
        "skip_verification": bool(current_app.config.get("SKIP_FACE_VERIFICATION")),
    }
