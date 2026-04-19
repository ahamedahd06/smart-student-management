# Emotion model training (Google Colab) — 4 classes

This project expects a **Keras** model that classifies **grayscale 48×48** face crops into:

| Index | Label   |
|-------|---------|
| 0     | angry   |
| 1     | happy   |
| 2     | neutral |
| 3     | sad     |

The default `label_map` in the Flask app matches `backend/ml/label_map.example.json`. If your last layer uses a **different class order**, export your own `label_map.json` and set `EMOTION_LABEL_MAP_PATH`.

## 1. Dataset strategy (practical for a final-year project)

**Primary choice:** [FER2013](https://www.kaggle.com/datasets/msambare/fer2013) (often accessed via Kaggle in Colab).

**Original FER labels:** angry, disgust, fear, happy, sad, surprise, neutral (7 classes).

**Mapping to your 4 classes:**

- `happy` ← `happy`
- `sad` ← `sad`
- `neutral` ← `neutral`
- `angry` ← `angry`
- **Drop** `disgust`, `fear`, `surprise` (do not include those folders / indices in training)

This keeps labels academically honest (no random relabelling to “fake” emotions).

**Optional merge (only if you need more samples):** map `surprise` → `neutral`. Document this explicitly in your report if you do it.

## 2. Folder layout for Colab training

```text
/data/fer4/
  angry/
  happy/
  neutral/
  sad/
```

Each folder contains `.png` (or `.jpg`) crops **already face-centred** if possible (Viola–Jones or a face detector in preprocessing).

## 3. Preprocessing (match Flask inference)

In Flask (`app/ml/preprocess.py`), inference uses:

- RGB `PIL.Image` → **grayscale**
- Resize **48 × 48**
- `float32` in **[0, 1]** (divide by 255)
- Tensor shape **(1, 48, 48, 1)** NHWC

Your Colab `tf.data` pipeline must apply the **same** steps before feeding the network.

## 4. Train / validation split

- Stratified split **80 / 20** (or 70 / 30) **per class**
- Seed (e.g. `42`) for reproducibility
- Report accuracy + per-class precision/recall in your viva

## 5. Augmentation (optional but recommended)

On the training set only:

- Random horizontal flip (use carefully; FER faces are mostly frontal — mild flips only)
- Small random brightness / contrast
- Small random shift / zoom

Avoid heavy distortion that breaks facial structure.

## 6. Model architecture (Colab-friendly)

A compact CNN is enough for FER-style inputs, for example:

- `Conv2D(32, 3×3)` → BN → ReLU → MaxPool
- `Conv2D(64, 3×3)` → BN → ReLU → MaxPool
- `Conv2D(128, 3×3)` → BN → ReLU → MaxPool
- `GlobalAveragePooling2D`
- `Dense(128, relu)` + Dropout(0.4)
- `Dense(4, softmax)`  ← **four units**

Alternatively **MobileNetV2** (ImageNet weights) with grayscale tripled to 3 channels is common; keep input 48×48 or resize to 96×96, but **change Flask preprocessing to match** if you change input size.

## 7. Export for Flask

In Colab, after training:

```python
model.save("emotion_model.keras")  # preferred TF 2.x format
# or
model.save("emotion_model.h5")
```

Download `emotion_model.keras` (or `.h5`) plus `label_map.json`.

Place files locally, for example:

```text
backend/models/emotion_model.keras
backend/ml/label_map.json
```

Set environment variables:

```env
EMOTION_MODEL_PATH=backend/models/emotion_model.keras
EMOTION_LABEL_MAP_PATH=backend/ml/label_map.json
```

## 8. Viva checklist

- What data you used, and **exactly** how 7 FER classes became 4.
- Input tensor shape and normalisation (**must match** `preprocess.py`).
- How you export the model and where the Flask app loads it.
- Limitations (lighting, pose, dataset bias) — mention honestly.
