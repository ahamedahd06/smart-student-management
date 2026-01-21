# System Design

## Architecture (Text Diagram)
```
                +-------------------------+
                |      Streamlit UI      |
                |  app.py (Tabs/Pages)   |
                +-----------+-------------+
                            |
            +---------------+---------------+
            |                               |
  +---------v----------+          +---------v----------+
  |     db.py          |          |   model_utils.py   |
  | SQLite operations  |          | OpenCV + Keras ML  |
  +---------+----------+          +---------+----------+
            |                               |
  +---------v----------+          +---------v----------+
  |   data/students.db |          |  emotion_model.*   |
  |     (SQLite)       |          |  (Keras model)     |
  +--------------------+          +--------------------+
```

## Modules

### app.py (UI)
- Streamlit interface with tabs: Students, Attendance + Emotion, Dashboard, Reports.
- Handles validation, error messaging, and UI state.
- Loads the emotion model and routes images through face detection + inference.
- Computes risk scoring from recent attendance and emotion logs.

### db.py (Persistence Layer)
- Initializes and manages SQLite tables.
- Provides CRUD for students.
- Stores unified logs (attendance + emotion).
- Returns records as dictionaries for easy UI rendering.

### ml/model_utils.py (ML Utilities)
- Loads Keras model (`emotion_model.keras` or `.h5`).
- Detects a face using OpenCV Haar cascade.
- Preprocesses to grayscale 48x48 and normalizes.
- Predicts emotion with confidence scores.
- Includes a stub for future face recognition (phase 2).

## Database Schema

**students**
- `student_id` (TEXT, PK)
- `name` (TEXT, NOT NULL)
- `batch` (TEXT)
- `email` (TEXT)
- `phone` (TEXT)
- `created_at` (TEXT, default CURRENT_TIMESTAMP)

**logs** (unified attendance + emotion)
- `id` (INTEGER, PK, AUTOINCREMENT)
- `student_id` (TEXT, FK -> students.student_id)
- `date` (TEXT, NOT NULL, ISO date)
- `attendance` (TEXT, NOT NULL, Present/Absent)
- `emotion` (TEXT, nullable)
- `confidence` (REAL, nullable)
- `created_at` (TEXT, default CURRENT_TIMESTAMP)

## Workflow
1. User adds students to the registry.
2. User logs attendance and optionally uploads a face image.
3. If a model is available, the system detects a face and predicts emotion.
4. The log (attendance + emotion) is stored in SQLite.
5. The dashboard aggregates logs, visualizes trends, and computes risk levels.

## Risk Scoring
The system uses a transparent rule-based model on the most recent 7 logs:
- High: absences >= 3 AND negative emotions >= 2
- Medium: absences >= 2 OR negative emotions >= 2
- Low: otherwise

Negative emotions are configurable in `app.py`.
