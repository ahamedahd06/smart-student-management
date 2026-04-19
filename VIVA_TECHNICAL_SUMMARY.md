# Smart Student Management System (SSMS)
## Technical Summary — Viva Preparation Document

---

## 1. System Overview

**Full Title:** Smart Student Management System with Facial Recognition and ML-Based Emotion Detection to Support Student Retention

**Purpose:** A web-based academic management platform that uses AI-powered facial recognition for automated attendance verification and machine learning-based emotion detection to monitor student engagement and wellbeing. The system supports early intervention for at-risk students through retention alerts and structured interventions.

**Key Innovation:** Unlike traditional attendance systems that use manual roll-calls or ID cards, SSMS uses real-time webcam-based facial detection (OpenCV) combined with a Convolutional Neural Network (CNN) emotion classifier (TensorFlow/Keras) to simultaneously verify identity and assess emotional state during check-in.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit (Python) | Web application framework with real-time UI |
| **Database** | SQLite with WAL mode | Lightweight relational database, file-based |
| **Face Detection** | OpenCV (Haar Cascade) | Real-time frontal face detection from webcam |
| **Emotion Classification** | TensorFlow / Keras CNN | 4-class emotion prediction (angry, happy, neutral, sad) |
| **Image Processing** | Pillow (PIL) | Image manipulation and preprocessing |
| **Authentication** | bcrypt | Secure password hashing and verification |
| **Language** | Python 3.10+ | Core programming language |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    STREAMLIT UI                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  app.py   │  │ theme.py │  │  views_*.py      │   │
│  │ (routing) │  │ (design) │  │ (role portals)   │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────┤
│                  BUSINESS LOGIC                       │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ auth_util.py  │  │ seed.py    │  │ catalog.py  │  │
│  │ registration  │  │ branding   │  │ database.py │  │
│  └──────────────┘  └────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│                    ML PIPELINE                        │
│  ┌──────────────────────────────────────────────┐    │
│  │ emotion_infer.py                              │    │
│  │  1. OpenCV Haar Cascade → face detection      │    │
│  │  2. 48×48 grayscale preprocessing             │    │
│  │  3. CNN model prediction (4 classes)          │    │
│  │  4. Confidence scoring                        │    │
│  └──────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│                    DATA LAYER                        │
│  ┌──────────────────────────────────────────────┐    │
│  │ SQLite (ssms.db) — WAL mode, 9 tables         │    │
│  │ emotion_model.keras — CNN model (330K params)  │    │
│  │ label_map.json — class index mapping           │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 4. Database Schema (9 Tables)

### Core Tables
- **students** — Student profiles (student_code, name, email, course, year, status, attendance_rate, risk_level, gpa)
- **users** — Authentication (email, password_hash, role, student_row_id, approved, name). Roles: admin, lecturer, student

### Attendance & Sessions
- **class_sessions** — Lecture/lab/tutorial scheduling (module_code, module_name, session_type, session_name, date, time)
- **attendance_records** — Check-in records linked to students and sessions, including detected emotion and confidence

### ML & Wellbeing
- **emotion_logs** — Historical emotion data per student with context and confidence
- **retention_alerts** — Risk alerts with severity levels (low, medium, high, critical) and resolution tracking

### Interventions & Finance
- **interventions** — Support actions assigned to lecturers with status tracking (open, in_progress, resolved)
- **fee_items** — Student fee line items with amounts and due dates
- **payments** — Payment records with method (Card, Bank Transfer, Cash) and references

### Key Relationships
```
users.student_row_id → students.id
attendance_records.student_row_id → students.id
attendance_records.session_id → class_sessions.id
emotion_logs.student_row_id → students.id
retention_alerts.student_row_id → students.id
fee_items.student_row_id → students.id
payments.student_row_id → students.id
payments.fee_item_id → fee_items.id
```

---

## 5. ML Pipeline — Emotion Detection

### Model Architecture (Sequential CNN)
```
Layer                          Output Shape         Parameters
─────────────────────────────────────────────────────────────
Conv2D (32 filters, 3×3)      (None, 48, 48, 32)   320
BatchNormalization             (None, 48, 48, 32)   128
ReLU                           (None, 48, 48, 32)   0
MaxPooling2D (2×2)             (None, 24, 24, 32)   0
Conv2D (64 filters, 3×3)      (None, 24, 24, 64)   18,496
BatchNormalization             (None, 24, 24, 64)   256
ReLU                           (None, 24, 24, 64)   0
MaxPooling2D (2×2)             (None, 12, 12, 64)   0
Conv2D (128 filters, 3×3)     (None, 12, 12, 128)  73,856
BatchNormalization             (None, 12, 12, 128)  512
ReLU                           (None, 12, 12, 128)  0
MaxPooling2D (2×2)             (None, 6, 6, 128)    0
GlobalAveragePooling2D         (None, 128)          0
Dropout                        (None, 128)          0
Dense (128 units)              (None, 128)          16,512
Dense (4 units, softmax)       (None, 4)            516
─────────────────────────────────────────────────────────────
Total parameters: 330,894 (1.26 MB)
Trainable parameters: 110,148
```

### Prediction Flow
1. **Capture** — Webcam image captured via Streamlit's `st.camera_input`
2. **Face Detection** — OpenCV Haar Cascade (`haarcascade_frontalface_default.xml`) detects frontal faces, returns bounding box coordinates
3. **Preprocessing** — Crop face region → convert to grayscale → resize to 48×48 → normalize to float32 [0,1] → reshape to (1, 48, 48, 1)
4. **Inference** — TensorFlow Keras model predicts probabilities for 4 emotion classes
5. **Result** — argmax selects highest probability class, confidence score extracted
6. **Storage** — Emotion label + confidence saved to both `attendance_records` and `emotion_logs`

### Label Mapping
| Index | Emotion |
|-------|---------|
| 0 | Angry |
| 1 | Happy |
| 2 | Neutral |
| 3 | Sad |

---

## 6. Role-Based Access Control

### Admin (admin@university.esu / admin123)
- Full student CRUD (Create, Read, Update, Delete)
- Lecturer approval/rejection workflow
- Attendance records with CSV export
- System-wide analytics dashboard
- Create and manage interventions
- Fee management (individual + bulk assignment)

### Lecturer (dr.sarah@university.esu / sarah123)
- Create and manage class sessions
- Browse all students with risk indicators
- Analytics (attendance trends, risk distribution, emotions)
- View and resolve retention alerts
- Manage assigned interventions

### Student (john.smith@university.esu / john123)
- Webcam-based facial check-in with emotion detection
- View personal attendance history
- View personal emotion logs with summaries
- View risk score and active alerts
- View fees and make payments (Card, Bank Transfer, Cash)

---

## 7. Key Features Summary

| Feature | Description | Technology |
|---------|------------|------------|
| Facial Recognition Check-In | Real-time face detection for attendance | OpenCV Haar Cascade |
| Emotion Detection | CNN-based mood classification during check-in | TensorFlow/Keras |
| Role-Based Portals | Separate dashboards per role | Streamlit + session state |
| Retention Alerts | Automated risk flagging system | SQLite queries |
| Interventions System | Structured support workflow | Admin → Lecturer pipeline |
| Fee Management | Fee assignment and payment tracking | SQLite + UI forms |
| Analytics Dashboard | Charts for attendance, risk, emotions | Streamlit charts |
| Lecturer Approval Workflow | Admin approval for new lecturers | Database flag (approved) |
| Password Security | bcrypt hashing with salt | bcrypt library |
| Data Export | CSV export of attendance records | Python CSV generation |

---

## 8. File Structure

```
PROJECT/
├── streamlit_ssms/          (Main application)
│   ├── app.py               — Entry point, auth, routing
│   ├── theme.py             — Design system, CSS, components
│   ├── views_student.py     — Student portal (5 tabs)
│   ├── views_lecturer.py    — Lecturer portal (5 tabs)
│   ├── views_admin.py       — Admin portal (6 tabs)
│   ├── database.py          — SQLite schema, migrations
│   ├── seed.py              — Demo data seeding
│   ├── auth_util.py         — bcrypt password hashing
│   ├── registration.py      — Student/lecturer registration
│   ├── branding.py          — System names, constants
│   ├── catalog.py           — Programme list
│   ├── emotion_infer.py     — ML pipeline (face + emotion)
│   ├── ml_preprocess.py     — Tensor preprocessing
│   ├── data/ssms.db         — SQLite database file
│   └── .streamlit/config.toml
├── backend/
│   ├── models/
│   │   └── emotion_model.keras  — Trained CNN model (1.26 MB)
│   └── ml/
│       └── label_map.json       — Emotion class mapping
└── requirements*.txt
```

---

## 9. Demo Accounts

| Role | Email | Password | Name |
|------|-------|----------|------|
| Admin | admin@university.esu | admin123 | Ahamed |
| Lecturer | dr.sarah@university.esu | sarah123 | Dr. Sarah Johnson |
| Student | john.smith@university.esu | john123 | John Smith (S001) |
| Student | emma.j@university.esu | emma123 | Emma Johnson (S002) |

---

## 10. How to Run

```bash
cd streamlit_ssms
pip install -r requirements.txt
pip install -r requirements-ml.txt    # For TensorFlow + OpenCV
streamlit run app.py
```

The app opens at `http://localhost:8501`. The database is auto-created and seeded on first run.
