# Smart Student Management System with Facial Recognition and ML-Based Emotion Detection to Support Student Retention

**Short name:** Smart Student Management System (SSMS)

This project delivers a **role-based web application** (Streamlit + SQLite) for:

- **Attendance** with webcam face capture at check-in  
- **ML-based emotion estimation** (4-class Keras model trained in **Google Colab**, exported to `backend/models/emotion_model.keras`)  
- **Retention support**: risk indicators, alerts, and interventions for staff  

The **primary runnable system** is under `streamlit_ssms/`. It auto-detects your Colab model and `backend/ml/label_map.json` when present.

---

## Run the application

```powershell
cd streamlit_ssms
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# For real emotion inference (TensorFlow + OpenCV), when you have disk space:
# pip install -r requirements-ml.txt
streamlit run app.py
```

Open the URL shown (usually `http://localhost:8501`).

- **Database:** `streamlit_ssms/data/ssms.db` (SQLite, created automatically; sample users seeded on first run).  
- **ML:** If `backend/models/emotion_model.keras` exists, check-in uses **48×48 grayscale** input matching `docs/COLAB_EMOTION_TRAINING.md` and the Flask preprocessor. Override paths with `SSMS_EMOTION_MODEL_PATH` and `SSMS_EMOTION_LABEL_MAP_PATH` if needed.

**Seeded demo accounts** (see `streamlit_ssms/seed.py`). Password rule: **lowercase first name + `123`** (e.g. `admin123`, `sarah123`).

| Role | What they do | Email | Password |
|------|----------------|--------|----------|
| **Administrator** | Full access: students, lecturer approvals, attendance, analytics, alerts | `admin@university.esu` | `admin123` |
| **Lecturer** | Teaching staff: sessions, monitoring, student support (no self check-in as student) | `dr.sarah@university.esu` | `sarah123` |
| **Student** | Check-in, own attendance, emotion log, risk view | `john.smith@university.esu` | `john123` |
| **Student** | (second demo account) | `emma.j@university.esu` | `emma123` |

**How to use roles**

1. Run `streamlit run app.py` and open the URL (e.g. `http://localhost:8501`).
2. On the landing page, choose **Administrator**, **Lecturer**, or **Student** → **Continue**.
3. **Sign in** with the email + password for that role (table above), or use **Register** for a new student/lecturer.
4. New **lecturers** must be **approved** by an administrator under **Lecturer approvals** before they can sign in.

**If login fails after editing passwords:** Restart the app once (demo hashes update from `seed.py` on startup). If it still fails, delete `streamlit_ssms/data/ssms.db` and restart to create a fresh database.

The admin sign-in screen always uses email **`admin@university.esu`** (password is not the email prefix; use **`admin123`** for the demo).

---

## Machine learning (Colab → local)

1. Train/export in Colab per **`docs/COLAB_EMOTION_TRAINING.md`**.  
2. Place **`emotion_model.keras`** in `backend/models/`.  
3. Place **`label_map.json`** in `backend/ml/` (see `label_map.example.json`).  
4. Install TensorFlow in the Streamlit venv (`requirements-ml.txt`) for inference.

---

## Optional: reduce project size on disk

- **Virtual environments** (`.venv` inside `streamlit_ssms/` and `backend/`) are the largest folders. They can be deleted; recreate with `python -m venv .venv` and `pip install -r requirements.txt` in each app folder you use.
- **`backend/`** may include ML weights under `backend/models/` — large but needed only if you run that API or copy the `.keras` file for Streamlit.

---

## Documentation

| File | Purpose |
|------|---------|
| `Interim.docx` | Interim report / scope |
| `docs/COLAB_EMOTION_TRAINING.md` | Dataset, 4-class mapping, Colab training, export |
| `streamlit_ssms/branding.py` | Official system title string for UI |
