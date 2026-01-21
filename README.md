# Smart Student Management System

Professional prototype for:
**"Smart Student Management System with Facial Recognition and ML-Based Emotion Detection for Student Retention Support"**

This project provides a Streamlit-based web UI with a SQLite backend and a TensorFlow/Keras
emotion detection model. It is designed to help lecturers and administrators monitor attendance,
track emotional signals, and identify students who may need early support.

## Features
- Student registry (add, update, delete, list)
- Attendance logging by date
- Emotion detection from uploaded face images (OpenCV + Keras model)
- Rule-based risk scoring (Low/Medium/High)
- Dashboard with charts and exportable reports (CSV)
- SQLite storage, no paid services

## Tech Stack
- UI: Streamlit + HTML/CSS (via `st.markdown`)
- DB: SQLite
- ML: TensorFlow/Keras
- Image processing: OpenCV

## Folder Structure
```
.
├── app.py
├── db.py
├── requirements.txt
├── SYSTEM_DESIGN.md
├── TESTING.md
├── assets/
│   └── styles.css
├── data/
│   └── students.db  (created on first run)
└── ml/
    ├── model_utils.py
    └── train_emotion_model_colab.ipynb
```

## Quick Start (Windows)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Quick Start (macOS/Linux)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Emotion Model Setup (Colab)
The app loads the model from:
- `ml/emotion_model.keras` (preferred)
- `ml/emotion_model.h5` (fallback)

Use the provided Colab notebook to train and export the model:
1. Open `ml/train_emotion_model_colab.ipynb` in Google Colab.
2. Run all cells to train a small CNN on the FER-2013 dataset.
3. Download `emotion_model.keras`.
4. Place it in the `ml/` folder next to `model_utils.py`.

If the model file is missing, the app will still run but emotion detection will be disabled.

## Risk Scoring (Explainable Rules)
The dashboard calculates risk from the most recent 7 logs:
- **High**: absences >= 3 AND negative emotions >= 2
- **Medium**: absences >= 2 OR negative emotions >= 2
- **Low**: otherwise

Negative emotions are configurable in `app.py` (`NEGATIVE_EMOTIONS`).

## Data and Security Notes
- Data is stored in `data/students.db` (SQLite).
- Uploaded images are processed in memory only and are not stored by default.

## Phase 2 (Planned)
Face recognition using embeddings is planned as a future enhancement. The current code includes
stub interfaces to keep the architecture ready for extension.
