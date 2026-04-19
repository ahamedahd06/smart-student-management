"""
Train the SSMS emotion CNN — aligned with streamlit_ssms/model_spec.py and emotion_infer.py.

Outputs:
  backend/models/emotion_model.keras
  backend/ml/label_map.json

Run from project root (folder that contains streamlit_ssms/ and backend/):

  pip install -r requirements-training.txt
  pip install -r streamlit_ssms/requirements-ml.txt

  python train_emotion_model.py
  python train_emotion_model.py --sample-train 0.5 --epochs 50
  python train_emotion_model.py --resume

Stopped mid-run? Use --resume if checkpoints exist under backend/models/checkpoints/.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, cast

os.environ["TF_USE_LEGACY_KERAS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_SSMS = ROOT / "streamlit_ssms"
if str(_SSMS) not in sys.path:
    sys.path.insert(0, str(_SSMS))

from model_spec import (  # noqa: E402
    CLASS_NAMES,
    FER7_TO_4,
    build_keras_model,
    label_map_json_text,
)

OUT_DIR = ROOT / "backend" / "models"
CKPT_DIR = OUT_DIR / "checkpoints"
OUT_MODEL = OUT_DIR / "emotion_model.keras"
LAST_CKPT = CKPT_DIR / "emotion_train_last.keras"
BEST_CKPT = CKPT_DIR / "emotion_train_best.keras"
LABEL_OUT = ROOT / "backend" / "ml" / "label_map.json"


def _verify_saved_model_matches_app() -> None:
    """Load saved .keras and run one forward pass using the same preprocess as the Streamlit app."""
    print("\n[verify] Checking saved model matches emotion_infer preprocessing...")
    import tensorflow as tf

    keras = cast(Any, tf).keras
    if not OUT_MODEL.is_file():
        print("  (skip — model file missing)")
        return
    model = keras.models.load_model(str(OUT_MODEL))
    rng = np.random.RandomState(0)
    face_gray = (rng.rand(90, 90) * 255).astype(np.uint8)
    # Import app-side preprocess (same as webcam pipeline)
    from emotion_infer import _preprocess_face  # noqa: E402

    x = _preprocess_face(face_gray)
    assert x.shape == (1, 48, 48, 1), x.shape
    out = model.predict(x, verbose=0)
    assert out.shape == (1, len(CLASS_NAMES)), out.shape
    s = float(out.sum())
    assert abs(s - 1.0) < 1e-2, s
    print(f"  OK — softmax output shape {out.shape}, sum≈1 (got {s:.4f})")
    print("  Restart Streamlit so emotion_infer reloads the new weights.")


def main() -> None:
    p = argparse.ArgumentParser(description="Train SSMS FER→4-class emotion model")
    p.add_argument("--epochs", type=int, default=80, help="Max epochs (EarlyStopping usually stops earlier)")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--resume", action="store_true", help=f"Continue from {LAST_CKPT} if it exists")
    p.add_argument("--quick", action="store_true", help="Use only 15% of train data for a fast smoke test")
    p.add_argument(
        "--sample-train",
        type=float,
        default=1.0,
        metavar="F",
        help="Random fraction of training set (0-1), e.g. 0.45 for faster runs",
    )
    p.add_argument("--no-verify", action="store_true", help="Skip post-save verification")
    args = p.parse_args()

    print("=" * 56)
    print(" SSMS — emotion model training (matches model_spec.py + emotion_infer)")
    print("=" * 56)

    print("\n[1/5] Loading FER2013 (Hugging Face)...")
    from datasets import load_dataset

    ds = load_dataset("Aaryan333/fer2013_train_publicTest_privateTest")

    def parse_split(split):
        images, labels = [], []
        for row in split:
            img = row["image"].convert("L")
            arr = np.array(img, dtype=np.float32).reshape(48, 48, 1) / 255.0
            images.append(arr)
            lab = int(row["label"])
            if lab not in FER7_TO_4:
                raise ValueError(f"Unexpected FER label index {lab}; expected 0–6.")
            labels.append(FER7_TO_4[lab])
        return np.array(images), np.array(labels)

    print("[2/5] Parsing images...")
    X_train, y_train = parse_split(ds["train"])
    pub = parse_split(ds["publicTest"])
    priv = parse_split(ds["privateTest"])
    X_test = np.concatenate([pub[0], priv[0]])
    y_test = np.concatenate([pub[1], priv[1]])

    if args.quick:
        n = max(1000, int(len(X_train) * 0.15))
        X_train, y_train = X_train[:n], y_train[:n]
        print(f"  [quick] Using first {n} train images only.")
    elif args.sample_train < 1.0:
        f = max(0.05, min(1.0, float(args.sample_train)))
        rng = np.random.RandomState(42)
        idx_s = rng.permutation(len(X_train))[: int(len(X_train) * f)]
        X_train, y_train = X_train[idx_s], y_train[idx_s]
        print(f"  [sample-train] Using random {100.0 * f:.0f}% subset → {len(X_train)} images")

    print(f"  Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

    from sklearn.utils.class_weight import compute_class_weight

    cw = compute_class_weight("balanced", classes=np.array([0, 1, 2, 3]), y=y_train)
    class_weights = {i: float(w) for i, w in enumerate(cw)}
    print(f"  Class weights: {{{', '.join(f'{CLASS_NAMES[i]}: {w:.2f}' for i, w in class_weights.items())}}}")

    angry_mask = y_train == 0
    X_angry_flip = X_train[angry_mask][:, :, ::-1, :]
    y_angry_flip = y_train[angry_mask]
    X_train = np.concatenate([X_train, X_angry_flip])
    y_train = np.concatenate([y_train, y_angry_flip])
    print(f"  After angry flip aug: {X_train.shape[0]} images")

    rng_shuffle = np.random.default_rng(42)
    idx = rng_shuffle.permutation(len(X_train))
    X_train, y_train = X_train[idx], y_train[idx]

    print("\n[3/5] Model (from model_spec.build_keras_model)...")
    import tensorflow as tf

    keras = cast(Any, tf).keras
    intra = int(os.getenv("TF_INTRA_OP_THREADS", "2"))
    inter = int(os.getenv("TF_INTER_OP_THREADS", "2"))
    try:
        tf.config.threading.set_intra_op_parallelism_threads(intra)
        tf.config.threading.set_inter_op_parallelism_threads(inter)
    except Exception:
        pass

    initial_epoch = 0
    if args.resume and LAST_CKPT.is_file():
        print(f"  Resuming from {LAST_CKPT}")
        model = keras.models.load_model(LAST_CKPT)
        ep_file = CKPT_DIR / "last_epoch.txt"
        if ep_file.is_file():
            initial_epoch = int(ep_file.read_text().strip())
            print(f"  initial_epoch = {initial_epoch}")
    else:
        if args.resume:
            print(f"  No checkpoint at {LAST_CKPT} — training from scratch.")
        model = build_keras_model()
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0005),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        print(f"  Params: {model.count_params():,}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    lr_cb = keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=4, verbose=1, min_lr=1e-6
    )
    es_cb = keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        mode="max",
        patience=18,
        verbose=1,
        restore_best_weights=True,
    )
    ck_best = keras.callbacks.ModelCheckpoint(
        filepath=str(BEST_CKPT),
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    )

    class SaveLastEpoch(keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            epoch1 = epoch + 1 + initial_epoch
            self.model.save(str(LAST_CKPT))
            CKPT_DIR.mkdir(parents=True, exist_ok=True)
            (CKPT_DIR / "last_epoch.txt").write_text(str(epoch1))

    print(f"\n[4/5] Training (max {args.epochs} epochs)...")
    model.fit(
        X_train,
        y_train,
        validation_data=(X_test, y_test),
        epochs=args.epochs,
        initial_epoch=initial_epoch,
        batch_size=args.batch_size,
        class_weight=class_weights,
        callbacks=[lr_cb, es_cb, ck_best, SaveLastEpoch()],
        verbose=1,
    )

    if BEST_CKPT.is_file():
        try:
            model = keras.models.load_model(BEST_CKPT)
            print(f"\nLoaded best weights from {BEST_CKPT}")
        except Exception as e:
            print(f"  (Could not reload best checkpoint: {e})")

    print("\n[5/5] Evaluating...")
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"  Val loss: {loss:.4f}  |  Overall accuracy: {acc:.2%}")

    preds = np.argmax(model.predict(X_test, verbose=0), axis=1)
    print("  Per-class recall (correct / true):")
    for i, name in enumerate(CLASS_NAMES):
        mask = y_test == i
        if mask.sum() > 0:
            print(f"    {name:>8}: {(preds[mask] == i).mean():.2%} ({int(mask.sum())} samples)")

    LABEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    LABEL_OUT.write_text(label_map_json_text(), encoding="utf-8")
    print(f"\n  Wrote {LABEL_OUT}")

    model.save(str(OUT_MODEL))
    print(f"\nSaved production model: {OUT_MODEL}")

    if not args.no_verify:
        _verify_saved_model_matches_app()

    print("=" * 56)
    print(" DONE")
    print("=" * 56)


if __name__ == "__main__":
    main()
