"""
SSMS emotion model — single source of truth for training and inference.

- Input: 48×48×1 grayscale, values in [0, 1] (float32), same as emotion_infer._preprocess_face.
- Output: 4-way softmax — indices match backend/ml/label_map.json.

Keep this file in sync with train_emotion_model.py (training) and emotion_infer.py (deployment).
"""
from __future__ import annotations

# Class index → name (must match backend/ml/label_map.json)
CLASS_NAMES: tuple[str, ...] = ("angry", "happy", "neutral", "sad")
NUM_CLASSES = len(CLASS_NAMES)
INPUT_SHAPE = (48, 48, 1)

# FER-2013 7 labels → our 4 classes (same mapping as training script)
# FER: 0=Angry, 1=Disgust, 2=Fear, 3=Happy, 4=Sad, 5=Surprise, 6=Neutral
FER7_TO_4: dict[int, int] = {
    0: 0,  # angry → angry
    1: 0,  # disgust → angry (merge)
    2: 3,  # fear → sad (merge)
    3: 1,  # happy → happy
    4: 3,  # sad → sad
    5: 2,  # surprise → neutral
    6: 2,  # neutral → neutral
}


def label_map_json_text() -> str:
    return (
        "{\n"
        + ",\n".join(f'  "{i}": "{CLASS_NAMES[i]}"' for i in range(NUM_CLASSES))
        + "\n}\n"
    )


def build_keras_model():
    """CNN used for training and saved as backend/models/emotion_model.keras."""
    from tensorflow import keras

    return keras.Sequential(
        [
            keras.layers.Input(shape=INPUT_SHAPE),
            keras.layers.Conv2D(32, (3, 3), padding="same"),
            keras.layers.BatchNormalization(),
            keras.layers.ReLU(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            keras.layers.Conv2D(64, (3, 3), padding="same"),
            keras.layers.BatchNormalization(),
            keras.layers.ReLU(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            keras.layers.Conv2D(128, (3, 3), padding="same"),
            keras.layers.BatchNormalization(),
            keras.layers.ReLU(),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Dropout(0.25),
            keras.layers.GlobalAveragePooling2D(),
            keras.layers.Dense(256, activation="relu"),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(NUM_CLASSES, activation="softmax"),
        ]
    )
