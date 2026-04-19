# Smart Student Management System (SSMS)  
## Technical documentation for dissertation chapters (3 & 8)

**Repository layout (relevant roots):**

- `streamlit_ssms/` — entire Streamlit application (UI, DB access, ML inference, analytics).
- `streamlit_ssms/data/ssms.db` — default SQLite database (override with env `SSMS_SQLITE_PATH`).
- `backend/models/emotion_model.keras` — trained Keras model (optional at runtime).
- `backend/ml/label_map.json` — softmax index → emotion label (4 classes).
- `train_emotion_model.py` — project root; offline training script (not started by Streamlit).

**Formal titles (from `streamlit_ssms/branding.py`):**

- Short: *Smart Student Management System*
- Long: *Smart Student Management System with Facial Recognition and ML-Based Emotion Detection to Support Student Retention*
- Browser title (`PAGE_TITLE`): *Smart Student Management System | Retention Support*

---

## 1. Frontend details

### 1.1 Technology and pattern

- **Framework:** Streamlit (`streamlit_ssms/app.py`, `requirements.txt`).
- **Rendering model:** Server-driven reruns; state in `st.session_state` (e.g. `user`, `auth_portal`, `db_ready`).
- **Styling:** Global dark theme and component snippets via `theme.py` (`inject_theme`, colour constants, `page_header`, `card_start` / `card_end`, `stat_row`, `badge`, etc.).
- **Rich HTML blocks:** `st.markdown(..., unsafe_allow_html=True)` for cards and banners (student check-in result, admin lists). **Important:** multi-line markdown strings with heavy indentation can be parsed as *code blocks* by Streamlit; the check-in success card was refactored to **concatenated single-line HTML** in `views_student.py` (`_render_checkin_emotion_result`) to avoid a “white box” of raw HTML.

### 1.2 Main pages and navigation

**Entry:** `streamlit run app.py` from `streamlit_ssms/` (see `app.py` docstring).

**Unauthenticated flow (`app.py`):**

1. **Role landing** — `_role_landing()`: three primary buttons (Administrator, Lecturer, Student). Sets `st.session_state.auth_portal` to `admin` | `lecturer` | `student` and reruns.
2. **Back** — resets `auth_portal` to `None`.
3. **Role panels** — `_admin_panel`, `_student_panel`, `_lecturer_panel`: sign-in / register forms.

**Authenticated shell (`_render_portal`):**

- Top banner (system name, role, welcome name, **Sign out**).
- **Sign out** clears `st.session_state.user` and reruns.
- **Router:** `user["role"]` → `render_student_portal` | `render_lecturer_portal` | `render_admin_portal` (`views_student.py`, `views_lecturer.py`, `views_admin.py`).

### 1.3 Important UI files

| File | Responsibility |
|------|----------------|
| `streamlit_ssms/app.py` | Page config, DB init + seed once, login, portal routing. |
| `streamlit_ssms/theme.py` | CSS injection, layout helpers, chart chrome (`chart_header` / `chart_footer`). |
| `streamlit_ssms/branding.py` | System names, admin email constant, page title. |
| `streamlit_ssms/catalog.py` | Programme list for registration/admin student form. |
| `streamlit_ssms/views_student.py` | Student tabs: check-in (camera + ML), attendance, emotions, risk, fees. |
| `streamlit_ssms/views_lecturer.py` | Lecturer tabs: sessions, students, analytics, alerts, interventions. |
| `streamlit_ssms/views_admin.py` | Admin tabs: students, lecturers, attendance export, analytics, interventions, fees. |

---

## 2. Backend details (logic — no separate API tier)

All “backend” behaviour runs **in-process** with Streamlit: Python functions + `sqlite3` + optional TensorFlow/OpenCV.

### 2.1 Important Python modules

| Module | Role |
|--------|------|
| `database.py` | `get_connection()` context manager; `init_db()` schema + migrations (`_migrate_users_columns`, `_repair_admin_account`, etc.); WAL, `busy_timeout`, configurable connect timeout (`SSMS_SQLITE_TIMEOUT`). |
| `auth_util.py` | `hash_password`, `verify_password` (bcrypt). |
| `registration.py` | `register_new_student`, `register_new_lecturer`, `approve_lecturer`, `reject_lecturer`, optional `SSMS_REQUIRE_ESU_EMAIL`. |
| `seed.py` | `seed_if_empty()` — inserts demo data only when `users` count is zero. |
| `emotion_infer.py` | Face detection + preprocessing + Keras load/cache + `predict_emotion_full` / stubs. |
| `model_spec.py` | CNN definition, 4-class names, FER→4 mapping, label JSON text. |
| `analytics_util.py` | SQL-backed chart series + documented fallbacks for empty DB. |
| `train_emotion_model.py` (root) | Offline training; writes `backend/models` + `backend/ml`. |

### 2.2 Authentication flow (truthful, file-grounded)

1. **Startup:** `app.py` `main()` → if `db_ready` not set: `init_db()` then `seed_if_empty()` (`database.py`, `seed.py`).
2. **Admin sign-in (`_admin_panel`):** email fixed/displayed as `ADMIN_LOGIN_EMAIL` from `branding.py` (currently `admin@university.esu`). Query `users` where `role='admin'`; `verify_password` (`auth_util.py`). On success `_set_user` stores `id`, `email`, `role`, `student_row_id`, `display_name`.
3. **Student / lecturer sign-in (`_sign_in`):**  
   - Pending lecturer: query `users` with `role='lecturer'` and `approved=0`; if password matches, show warning and stop.  
   - Else: fetch user with matching email + role and lecturer approved filter; verify password; `_set_user`.
4. **Registration:** forms in `app.py` call `register_new_student` / `register_new_lecturer` (`registration.py`) — inserts `students` + `users` (student immediate; lecturer `approved=0`).
5. **Password storage:** only bcrypt hashes in `users.password_hash` — never plaintext in DB.

### 2.3 Attendance flow

1. **Prerequisites:** `class_sessions` rows exist (created by lecturer in `views_lecturer._sessions` — `INSERT INTO class_sessions`).
2. **Student check-in (`views_student._check_in`):**  
   - Loads sessions and current student row (`students` via `student_row_id`).  
   - User selects session (`st.selectbox` over session labels).  
   - `st.camera_input` → `img.getvalue()` → bytes.  
   - `predict_emotion_full(bytes)` (`emotion_infer.py`): Haar face detect → optional Keras 4-class prediction or stub → dict with `emotion`, `confidence`, `probs`, `bbox`, `tf_model`, `note`.  
   - UI: `_render_checkin_emotion_result` shows success/error under camera; **Confirm & Save** runs two inserts in one connection:  
     - `attendance_records` (`student_row_id`, `session_id`, `module_code`, `session_label`, `check_in_time`, `status='present'`, `emotion`, `emotion_confidence`)  
     - `emotion_logs` (`student_row_id`, `logged_at`, `context`, `emotion`, `confidence`)  
   - **Note:** `session_label` is stored as `row['session_name']` from the selected session dict (code path in `views_student.py`).

### 2.4 Alerts and interventions flow

**Retention alerts (`retention_alerts` table):**

- Seeded example in `seed.py` for one high-risk student.
- **Student view:** `views_student._risk` reads `retention_alerts` for `student_row_id`, renders `alert_card` HTML.
- **Lecturer view:** `views_lecturer._alerts` lists active vs resolved alerts with optional resolve note update (SQL `UPDATE` in same file).

**Interventions (`interventions` table):**

- **Admin:** `views_admin._interventions` expander form → `INSERT INTO interventions` with fields `student_code`, `type`, `severity`, `description`, `action_taken`, `assigned_to`, `status` — code uses **`"in_progress"`** as initial status (line ~183); table default in `database.py` schema is `'open'` — minor inconsistency if rows are created outside this form.
- **Lecturer:** `views_lecturer._interventions` lists rows where `assigned_to` matches display name, email, or local-part of email (`_cnt_iv` uses same matching for tab badge count).

### 2.5 Analytics flow

- **Admin** `views_admin._analytics` and **Lecturer** `views_lecturer._analytics` import **`analytics_util.py`**.
- **Programme attendance chart:** `module_programme_attendance_chart(5)` — SQL `GROUP BY students.course` with `AVG(attendance_rate)`; if no course data, **fixed demo percentages** for up to five labels (`PROGRAMMES` + `"Business Administration"`).
- **Emotion distribution:** `emotion_sentiment_chart()` — reads `emotion_logs.emotion`, else `attendance_records.emotion`; maps happy→Positive, angry/sad→Negative, else Neutral; if no rows returns **hardcoded** `{8,4,2}`.
- **Weekly trends:** `weekly_checkin_trend(5)` — SQL on `attendance_records` by ISO week (`strftime('%Y-%W', check_in_time)`); pairs with `retention_alerts` counts per week; if no attendance weeks, **hardcoded** series (see `analytics_util.py` lines 97–98).
- **Risk bars:** live `COUNT(*)` from `students` by `risk_level` (admin + lecturer).

### 2.6 “API” / action flow without REST

Each **button or form submit** maps to immediate Python:

- **Pattern:** `if st.button(...):` or `if st.form_submit_button(...):` → `with get_connection() as c:` → `c.execute(...)` → `st.rerun()` or `st.success`.
- **No** OpenAPI/REST layer; **no** CSRF token beyond Streamlit’s session model.

---

## 3. Database details

### 3.1 Engine and file

- **SQLite 3**, file path from `get_db_path()` (`database.py`): default **`streamlit_ssms/data/ssms.db`**.
- **Journal:** `PRAGMA journal_mode=WAL`; **`PRAGMA busy_timeout=30000`**; connect `timeout` from `SSMS_SQLITE_TIMEOUT` (default 30s).

### 3.2 Tables (from `init_db()` in `database.py`)

| Table | Purpose |
|-------|---------|
| `students` | Student profile: `student_code`, `name`, `email`, `course`, `year`, `status`, `attendance_rate`, `risk_level`, `gpa`, `created_at`. |
| `users` | Login accounts: `email`, `password_hash`, `role` (`admin`|`lecturer`|`student`), `student_row_id` (nullable; links student users), migrated `approved`, `name`. |
| `class_sessions` | Scheduled classes: `module_code`, `module_name`, `session_type`, `session_name`, `session_date`, `session_time`. |
| `attendance_records` | Check-ins: links `student_row_id`, optional `session_id`, `module_code`, `session_label`, `check_in_time`, `status`, `emotion`, `emotion_confidence`. |
| `emotion_logs` | Emotion history per student: `logged_at`, `context`, `emotion`, `confidence`. |
| `retention_alerts` | Wellbeing/attendance alerts: `severity`, `message`, `resolved`, `resolution_note`, `created_at`. |
| `interventions` | Staff cases: `student_code`, `type`, `severity`, `description`, `action_taken`, `assigned_to`, `status`, `created_at`. |
| `fee_items` | Fee lines per student: `description`, `amount`, `due_date`. |
| `payments` | Payments: `fee_item_id`, `amount`, `method`, `reference`, `paid_at`. |

### 3.3 Key fields and relationships

- **`users.student_row_id`** → **`students.id`** (FK) for student logins only; admin/lecturer typically `NULL`.
- **`attendance_records.student_row_id`** → **`students.id`** (required).
- **`attendance_records.session_id`** → **`class_sessions.id`** (optional FK; still stored when check-in uses session row).
- **`emotion_logs.student_row_id`** → **`students.id`**.
- **`retention_alerts.student_row_id`** → **`students.id`**.
- **`fee_items.student_row_id`**, **`payments.student_row_id`** → **`students.id`**; **`payments.fee_item_id`** → **`fee_items.id`**.

### 3.4 Migrations / repair (same `database.py`)

- Add `users.approved`, `users.name` if missing.
- Legacy `students.department` drop attempt.
- Email domain normalization `@university.ac.uk` → `@university.esu`.
- Admin account repair / password migration for demo accounts (`_repair_admin_account`, `_upgrade_seeded_passwords_to_current_seed`, `_update_admin_name`).

---

## 4. Page-by-page explanation

### 4.1 Public / login (`app.py`)

| Who | What they see | Actions |
|-----|----------------|--------|
| Anyone | Role landing, branded hero | Choose Admin / Lecturer / Student |
| Anyone | Back from sub-login | Return to role landing |
| Admin | Email (fixed), password | Sign in → `_set_user` |
| Student | Tabs Sign in / Register | Register form → `register_new_student`; Sign in → `_sign_in("student")` |
| Lecturer | Tabs Sign in / Register | Register → pending; Sign in → approval check |

### 4.2 Student portal (`views_student.py`)

| Tab | Data shown | Actions |
|-----|--------------|--------|
| **Check-In** | `class_sessions` list; camera; ML result | Capture → inference → optional **Confirm & Save** → inserts `attendance_records` + `emotion_logs` |
| **My Attendance** | Own `attendance_records` + joined session info | Read-only table |
| **My Emotion Logs** | `emotion_logs` for student | Read-only cards |
| **My Risk & Alerts** | `students` risk fields + `retention_alerts` | Read-only (no student-side resolve in code reviewed) |
| **Payments** | `fee_items` + payment totals; `payments` history | Pay form → `INSERT payments` |

### 4.3 Lecturer portal (`views_lecturer.py`)

| Tab | Data shown | Actions |
|-----|--------------|--------|
| **Sessions** | All `class_sessions` + per-session present/absent counts | **Create session** → `INSERT class_sessions` |
| **Students** | All `students` + search | Read-only cards |
| **Analytics** | Stats + charts from `analytics_util` + live risk counts | Read-only |
| **Alerts** | `retention_alerts` joined to students | Resolve flow with `UPDATE` |
| **Interventions** | Filtered `interventions` | Read-only list for assignee |

### 4.4 Admin portal (`views_admin.py`)

| Tab | Data shown | Actions |
|-----|--------------|--------|
| **Students** | All `students` + search | **Add student** (+ optional `users` row); read-only grid |
| **Lecturers** | Pending from `list_pending_lecturers` | Approve / Reject → `registration` helpers |
| **Attendance** | Filtered `attendance_records` + student names | CSV export |
| **Analytics** | SQL aggregates + charts | Read-only |
| **Alerts & Interventions** | Interventions list + create form | **Create intervention** → `INSERT` |
| **Fees** | Students + fee tooling (see file for add/payment admin flows) | Inserts/updates per form |

---

## 5. Testing and verification

### 5.1 Automated tests in repo

- **No project-owned `tests/` or `pytest` suite** was found under the application tree (only third-party tests inside `.venv`).  
- **Therefore:** verification is **manual** and **process-level** (run app, click flows, inspect DB).

### 5.2 Real test cases (suggested — align with your viva log)

| ID | Case | Steps | Expected | Actual (fill after you run) |
|----|------|-------|----------|------------------------------|
| T1 | Fresh DB seed | Delete/rename `ssms.db`, start app once | Users/students/sessions seeded; admin login works with `SEED_PASSWORD_ADMIN` | |
| T2 | Admin login | `admin@university.esu` + seed password | Lands on admin tabs | |
| T3 | Student check-in | Student login → Check-In → photo → save | Rows in `attendance_records` and `emotion_logs` with same emotion/confidence | |
| T4 | No face path | Cover camera / no face | Red “No Face Detected” under camera | |
| T5 | ML vs stub | With `.keras` + TF installed vs without | `tf_model` True vs False; note field explains stub | |
| T6 | Lecturer approval | Register lecturer → admin approve → lecturer login | Lecturer can sign in after approve | |
| T7 | DB lock | Open `ssms.db` in DB Browser with write txn, start app | May wait or error until browser closed | |
| T8 | Training verify | Run `train_emotion_model.py` to completion | `[verify]` OK + files under `backend/` | |

### 5.3 Manual testing already implied by development (honest)

- Streamlit **rerun** behaviour after inserts.
- **Camera** capture on target browser/OS.
- **TensorFlow** import and `load_model` on Windows (environment-specific).
- **Markdown/HTML** rendering for student check-in card (fixed indentation issue).

### 5.4 Limitations (testing perspective)

- No **load** or **security** test harness (SQL injection relies on parameterized queries — good practice but not formally tested).
- **Concurrent users** not modelled; SQLite + Streamlit single-process is fine for demo, not for large production concurrency.
- **Cross-browser** webcam behaviour not enumerated in code.

---

## 6. Tools and frameworks used (grouped for report)

**Languages & runtime**

- Python 3.x

**Application / UI**

- Streamlit  
- HTML/CSS via `st.markdown` + `theme.py`

**Data**

- SQLite (`sqlite3`)  
- Optional: DB Browser for SQLite (external; causes locks if left open)

**Security**

- bcrypt (`auth_util.py`)

**Machine learning (optional runtime stack)**

- TensorFlow / Keras (`emotion_infer.py`, `model_spec.py`, `train_emotion_model.py`)  
- OpenCV (headless package in `requirements-ml.txt`)  
- Pillow  
- NumPy, pandas (Streamlit stack)

**Training-only**

- Hugging Face `datasets`  
- scikit-learn (`compute_class_weight` in `train_emotion_model.py`)

**IDE / quality**

- Cursor / VS Code  
- Pyright / Pylance (`pyrightconfig.json`, `.vscode/settings.json`)

**Version control (assumed)**

- Git (if used; not required by code)

---

## 7. Problems faced and changes made (chronological themes)

1. **SQLite “database is locked”** when external tools (e.g. DB Browser) held the file — mitigated with **WAL**, higher **connect timeout**, **`PRAGMA busy_timeout`**, and documented workflow (close external tool).
2. **IDE import resolution** for root `train_emotion_model.py` — fixed with **`pyrightconfig.json`** `executionEnvironments.extraPaths` and TensorFlow typing pattern (`cast(Any, tf).keras`).
3. **`get_connection` typing** — Pyright treated `@contextmanager` generator as invalid for `with`; fixed return type **`Iterator[sqlite3.Connection]`** (`database.py`).
4. **Emotion UI not visible** — results rendered below column layout; **moved inference UI under camera** (`views_student.py`) + `st.success` summary.
5. **Face detection robustness** — added **PIL decode fallback** and **multi-pass Haar** parameters (`emotion_infer.py`).
6. **Raw HTML “white box”** — Streamlit markdown code-block parsing on indented HTML; **flattened HTML string** for green card (`views_student.py`).
7. **Hardcoded analytics module codes** — replaced with **`analytics_util.py`** using real `students.course` / logs / weekly SQL with **documented fallbacks**.
8. **Training ↔ inference alignment** — centralized **`model_spec.py`**, `train_emotion_model.py` post-save verify using **`emotion_infer._preprocess_face`**.

---

## 8. Final evaluation and limitations (Chapter 8)

### 8.1 Strengths (evidence-based)

- **Coherent monolith** suitable for coursework: one codebase, clear folders, SQLite schema covering attendance + wellbeing + fees.
- **Real security baseline:** bcrypt hashing; parameterized SQL in reviewed paths.
- **Real ML path when enabled:** FER-aligned training script, exported Keras model, OpenCV face pipeline, 4-class softmax consistent with `model_spec.py` and `label_map.json`.
- **Graceful degradation:** heuristic stub when model or TF unavailable.
- **Operational clarity:** role separation, lecturer approval, seed data for demos.

### 8.2 Limitations (must be stated in a dissertation)

- **Scale & concurrency:** Single SQLite file + single Streamlit process; not architected for high concurrent write load or multi-region deployment.
- **Identity / data drift:** Application constants use **`@university.esu`**; manually edited DBs with **`.edu`** will break login until aligned.
- **Analytics truthfulness:** Charts use **real SQL where possible**, but **explicit placeholder series** exist when tables are empty (`analytics_util.py`) — must be labelled as **illustrative** in reports, not empirical research findings.
- **Payments:** recorded as rows only — **no** PSP integration, PCI scope, or fraud controls.
- **Interventions status:** admin create path uses **`in_progress`** string; schema default mentions **`open`** — reporting should note **status vocabulary** is not fully normalized across UI.
- **Emotion validity:** Webcam + Haar + small CNN on merged FER classes is a **prototype** indicator, not a clinical or proctoring-grade affective instrument.
- **Testing gap:** **No automated test suite** in the repository; claims of correctness should reference **manual test tables** (Section 5) and **training verification output** (`train_emotion_model.py` verify block).

### 8.3 Overall verdict (one paragraph, safe for academic tone)

The implemented SSMS is a **well-scoped educational prototype** that integrates a Streamlit front end, a normalized SQLite schema, and an optional TensorFlow/OpenCV emotion pipeline with an offline training path. It successfully demonstrates **role-based access**, **attendance capture with affective metadata**, and **basic reporting**, while honestly requiring **environment setup** for ML and **careful interpretation** of analytics when the database is sparse. It is **not** positioned as a production campus-wide ERP replacement; its value lies in **traceable engineering decisions** and a **clear separation** between measured records (`attendance_records`, `emotion_logs`) and demonstrative charts (`analytics_util` fallbacks).

---

*End of document. Adjust Section 5.2 “Actual” column with your own run results before submission.*
