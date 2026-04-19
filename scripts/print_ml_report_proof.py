"""
Emit dissertation-friendly text: ML class mapping, preprocessing contract,
optional Keras model summary + shape proof (no training).

Run from project root:

  python scripts/print_ml_report_proof.py

Requires TensorFlow only if backend/models/emotion_model.keras exists and
you want the model summary block; mapping/spec prints without TF.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SSMS = ROOT / "streamlit_ssms"
if str(_SSMS) not in sys.path:
    sys.path.insert(0, str(_SSMS))

os.environ.setdefault("TF_USE_LEGACY_KERAS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def main() -> None:
    from model_spec import CLASS_NAMES, FER7_TO_4, INPUT_SHAPE, build_keras_model

    fer_names = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")

    print("=" * 72)
    print(" SSMS - ML process proof (paste into report appendix or viva notes)")
    print("=" * 72)
    print(f"\nRepository root (this run): {ROOT}")
    print("\n--- Single source of truth ---")
    print(f"  streamlit_ssms/model_spec.py - CLASS_NAMES = {CLASS_NAMES}")
    print(f"  Input tensor shape (NHWC): (batch, {INPUT_SHAPE[0]}, {INPUT_SHAPE[1]}, {INPUT_SHAPE[2]})")
    print("  Value range: float32 in [0, 1] per pixel (grayscale)")

    print("\n--- FER-2013 7-way label -> 4-class index (training targets) ---")
    print(f"{'FER idx':<8} {'FER name':<12} -> 4-class idx  name")
    for i, name in enumerate(fer_names):
        j = FER7_TO_4[i]
        print(f"  {i:<6}   {name:<12} -> {j}              {CLASS_NAMES[j]}")

    label_paths = [ROOT / "backend" / "ml" / "label_map.json", ROOT / "backend" / "ml" / "label_map.example.json"]
    lp = next((p for p in label_paths if p.is_file()), None)
    print("\n--- label_map.json on disk ---")
    if lp:
        print(f"  Using: {lp}")
        with open(lp, encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
    else:
        print("  (no label_map.json yet - training writes backend/ml/label_map.json)")

    model_path = ROOT / "backend" / "models" / "emotion_model.keras"
    print("\n--- Trained weights file ---")
    print(f"  Expected path: {model_path}")
    print(f"  Present: {model_path.is_file()}")

    print("\n--- CNN definition (untrained architecture clone) ---")
    try:
        import tensorflow as tf

        m = build_keras_model()
        m.summary()
    except Exception as e:
        print(f"  (TensorFlow not available or error: {e})")

    if not model_path.is_file():
        print("\n--- Saved model forward pass ---")
        print("  Skipped (no emotion_model.keras). Train with: python train_emotion_model.py")
        return

    print("\n--- Saved model: summary + inference shape proof ---")
    try:
        import numpy as np
        import tensorflow as tf
        from typing import Any, cast

        keras = cast(Any, tf).keras
        model = keras.models.load_model(str(model_path))
        model.summary()
        from emotion_infer import _preprocess_face

        rng = np.random.RandomState(0)
        face = (rng.rand(90, 90) * 255).astype("uint8")
        x = _preprocess_face(face)
        out = model.predict(x, verbose=0)
        s = float(out.sum())
        print(f"\n  Preprocess output shape: {x.shape}  (must be (1, 48, 48, 1))")
        print(f"  Softmax output shape:    {out.shape}  (must be (1, {len(CLASS_NAMES)}))")
        print(f"  Softmax sum:             {s:.6f}  (expect ~ 1.0)")
        print("  Per-class probabilities:", dict(zip(CLASS_NAMES, [float(f"{p:.4f}") for p in out[0]])))
    except Exception as e:
        print(f"  Error loading or predicting: {e}")


if __name__ == "__main__":
    main()
