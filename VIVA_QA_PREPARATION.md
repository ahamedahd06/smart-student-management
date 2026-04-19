# SSMS Viva — Questions & Answers Preparation

---

## SECTION A: System Overview Questions

### Q1: "What is your project about? Give an overview."

**Answer:** My project is a Smart Student Management System — or SSMS — that uses AI to improve student retention in universities. The core innovation is that when a student checks in for a class, instead of signing a sheet or tapping an ID card, they use their webcam. The system uses OpenCV for real-time face detection and a trained Convolutional Neural Network to classify their emotion at the moment of check-in. This data is stored and analyzed — if a student starts showing patterns like frequent absences or negative emotions, the system flags them as at-risk and triggers retention alerts for lecturers to intervene early. It also handles administrative tasks like fee management, lecturer approvals, and analytics dashboards. The whole system has three role-based portals for Admin, Lecturer, and Student.

---

### Q2: "What problem does this solve?"

**Answer:** In universities, student disengagement is often detected too late — typically after a student has already failed or dropped out. Manual attendance is unreliable, and there's no systematic way to monitor student wellbeing at scale. My system solves this by:
1. **Automating attendance** through facial recognition, eliminating fraud and manual errors
2. **Detecting emotional patterns** over time to identify disengaged students before they drop out
3. **Creating a structured intervention workflow** where admins can assign support tasks to lecturers
4. **Providing analytics** that give staff a real-time overview of attendance trends, risk levels, and emotional distribution across the student body

---

### Q3: "Who are the target users?"

**Answer:** Three types of users:
- **Students** who check in using their face, view their attendance, emotion history, and make fee payments
- **Lecturers** who monitor their students, view analytics, resolve alerts, and manage assigned interventions
- **Administrators** who manage the entire system — student records, lecturer approvals, fee management, and create interventions

---

## SECTION B: Technical / Architecture Questions

### Q4: "Why did you choose this tech stack?"

**Answer:** I chose Python as the primary language because of its strong ecosystem for both web development and machine learning. Specifically:
- **Streamlit** was chosen over Flask or Django because it allows building interactive web apps entirely in Python with minimal boilerplate — it has built-in support for camera input, charts, forms, and session state, which are all critical for this project
- **SQLite** was chosen because it's serverless and file-based — no separate database server needed. It supports WAL (Write-Ahead Logging) mode for better concurrent reads, and for a university-scale system it's sufficient
- **OpenCV** was used for face detection because it provides pre-trained Haar Cascade classifiers that work in real-time without requiring GPU acceleration
- **TensorFlow/Keras** was used for the emotion model because it's the industry standard for deep learning and supports straightforward CNN architectures that are well-suited for image classification tasks

---

### Q5: "Explain your database design."

**Answer:** The database has 9 tables in SQLite:
- **students** and **users** are the core identity tables. Users handles authentication with bcrypt-hashed passwords and role-based access (admin, lecturer, student). Students have a foreign key linking back from users via `student_row_id`
- **class_sessions** stores scheduled classes with module codes, dates, and times
- **attendance_records** is the bridge table — when a student checks in, a record is created linking them to a session, with their emotion and confidence score attached
- **emotion_logs** provides a separate time-series log of all emotions detected, which can be analyzed independently of attendance
- **retention_alerts** flags at-risk students with severity levels (low to critical)
- **interventions** creates an assignable workflow for staff to take action on at-risk students
- **fee_items** and **payments** handle the financial aspect with a one-to-many relationship (multiple payments can be made against a single fee)

The schema uses foreign keys for referential integrity and includes migrations for backward compatibility.

---

### Q6: "How does the authentication work?"

**Answer:** Passwords are hashed using **bcrypt** with automatic salting — the `hash_password` function generates a unique salt for each password, and `verify_password` compares against the stored hash without ever storing plaintext. The system has three roles with different access levels controlled by the `role` column in the `users` table. Lecturers have an additional `approved` flag — when they register, `approved` is set to 0 and they can't log in until an admin approves them. Session state in Streamlit manages the logged-in user across page interactions.

---

### Q7: "How does the facial recognition work?"

**Answer:** The facial recognition pipeline has two stages:

**Stage 1 — Face Detection (OpenCV):**
- The webcam captures an image via Streamlit's camera input
- The image is decoded from bytes to a NumPy array using OpenCV
- It's converted to grayscale (since Haar Cascades work on grayscale)
- OpenCV's pre-trained Haar Cascade classifier (`haarcascade_frontalface_default.xml`) scans the image using a sliding window approach at multiple scales
- It returns bounding box coordinates (x, y, width, height) for detected faces
- We select the largest face if multiple are found

**Stage 2 — Emotion Classification (CNN):**
- The detected face region is cropped from the grayscale image
- It's resized to 48×48 pixels (the input size the model was trained on)
- Pixel values are normalized to [0, 1] range (float32)
- The tensor is reshaped to (1, 48, 48, 1) — batch size 1, single channel
- The CNN model outputs 4 probabilities via softmax (angry, happy, neutral, sad)
- We take the argmax as the predicted class and the corresponding probability as the confidence score

---

### Q8: "Explain your CNN model architecture."

**Answer:** It's a Sequential CNN with three convolutional blocks:
- **Block 1:** 32 filters (3×3) → BatchNorm → ReLU → MaxPool (2×2) — captures basic edges and textures
- **Block 2:** 64 filters (3×3) → BatchNorm → ReLU → MaxPool (2×2) — captures more complex patterns like eye/mouth shapes
- **Block 3:** 128 filters (3×3) → BatchNorm → ReLU → MaxPool (2×2) — captures high-level facial features

Then: GlobalAveragePooling2D (reduces spatial dimensions) → Dropout (prevents overfitting) → Dense(128) → Dense(4) with softmax for 4 emotion classes.

Total parameters: 330,894 (about 1.26 MB). BatchNormalization helps training stability and speed. Dropout reduces overfitting on small datasets. GlobalAveragePooling is preferred over Flatten as it reduces parameters dramatically.

---

### Q9: "Why only 4 emotion classes? Why not 7 (like FER2013)?"

**Answer:** The original FER2013 dataset has 7 classes (angry, disgust, fear, happy, sad, surprise, neutral), but some classes like "disgust" and "fear" have very few training samples and are difficult to distinguish even for humans. By reducing to 4 classes — angry, happy, neutral, sad — we get:
1. Better accuracy due to reduced class confusion
2. More balanced training data per class
3. More meaningful insights for the retention use case (a student being consistently "sad" or "angry" is more actionable than distinguishing "fear" from "surprise")

---

### Q10: "What are the limitations of your system?"

**Answer:**
1. **Emotion accuracy** — Even the best emotion models achieve ~65-70% accuracy on FER2013. Real-world webcam conditions (lighting, angle, background) make it harder
2. **Single face assumption** — The system detects the largest face; it doesn't verify that the face belongs to the logged-in student (it's face detection, not face identification/matching)
3. **Lighting dependency** — The Haar Cascade detector is sensitive to poor lighting conditions
4. **SQLite scalability** — For a production system with thousands of concurrent users, we'd need PostgreSQL or MySQL
5. **Static analytics** — Some chart data is placeholder/demo data rather than dynamically aggregated from the database
6. **No real payment gateway** — Payment processing is simulated in the UI, not connected to a real payment provider like Stripe
7. **Single-server deployment** — Streamlit runs as a single process; a production system would need horizontal scaling

---

### Q11: "How would you improve this system if you had more time?"

**Answer:**
1. **Face verification** — Add face embedding comparison (using FaceNet or ArcFace) to verify the student's identity matches their registered photo, preventing someone else checking in for them
2. **Real payment integration** — Connect to Stripe or a local payment gateway for actual transactions
3. **Automated risk scoring** — Use ML to automatically calculate risk scores based on attendance patterns, emotion trends, and academic performance, instead of manual flags
4. **Push notifications** — Email or SMS alerts when a student is flagged as high-risk
5. **Mobile app** — A companion mobile app for students to check in from their phones
6. **Larger emotion model** — Train on a larger dataset with data augmentation, or use a pre-trained model like VGGFace with transfer learning
7. **PostgreSQL migration** — For production scalability and concurrent access

---

## SECTION C: Implementation / Code Questions

### Q12: "How does the check-in flow work end-to-end?"

**Answer:**
1. Student logs in → Student portal opens → "Check-In" tab
2. Student selects their module/session from a dropdown
3. Webcam activates via `st.camera_input`
4. Student captures a photo
5. Photo bytes are sent to `predict_emotion_from_bytes()` in `emotion_infer.py`
6. OpenCV's Haar Cascade runs face detection — if no face found, shows "No Face Detected" error
7. If face found, it's cropped, preprocessed to 48×48 grayscale tensor, and fed to the Keras CNN
8. Model returns emotion label + confidence
9. UI shows green "Face Detected — Student Verified" banner with student details, emotion, and confidence
10. Student clicks "Confirm & Save"
11. System inserts into both `attendance_records` and `emotion_logs` tables
12. Page refreshes showing updated attendance

---

### Q13: "How does the intervention workflow operate?"

**Answer:**
1. Admin creates an intervention in the "Alerts & Interventions" tab — specifying student ID, type (Attendance/Emotional/Academic), severity, assigned lecturer, and description
2. The intervention appears in the assigned lecturer's portal under their "Interventions" tab — the tab shows a count badge of pending interventions
3. The lecturer can view the intervention details, add action notes, and mark it as resolved
4. Both admin and lecturer can track the status (open → in_progress → resolved)

This creates an accountability loop — the admin identifies at-risk students, assigns them to lecturers, and can verify that actions were taken.

---

### Q14: "How does the lecturer approval flow work?"

**Answer:**
1. A new lecturer registers through the "Lecturer Portal" → "Register" tab
2. Their account is created in the `users` table with `approved = 0`
3. If they try to log in, they see "Awaiting admin approval"
4. Admin logs in → "Lecturers" tab → sees pending approval cards
5. Admin clicks "Approve" or "Reject"
6. If approved, the `approved` flag is set to 1 and the lecturer can now log in
7. If rejected, the account is deleted

---

### Q15: "How is the UI built? Why not use a frontend framework?"

**Answer:** The UI is built entirely in Streamlit with extensive custom CSS injected via `st.markdown(unsafe_allow_html=True)`. I chose this approach because:
1. **Speed of development** — Streamlit lets you build interactive UIs in pure Python, no need for separate HTML/CSS/JS files
2. **Built-in widgets** — Camera input, file upload, charts, forms, tabs, and session state are all native Streamlit features
3. **Custom design system** — I created a reusable component library in `theme.py` with consistent cards, badges, stat rows, chart containers, alert cards, etc.
4. **Dark dashboard theme** — Full CSS override for a professional dark SaaS look with Inter font, custom colors, gradients, and hover effects

For a production system, a React or Next.js frontend with a REST API backend would be more scalable, but Streamlit was ideal for rapid prototyping and demonstration.

---

## SECTION D: Data & Security Questions

### Q16: "How do you handle sensitive data?"

**Answer:**
- Passwords are never stored in plaintext — they're hashed using bcrypt with automatic salting
- The database is a local SQLite file, not exposed to the internet
- Role-based access ensures students can only see their own data, lecturers see their assigned students, and only admins have full access
- Session state manages authentication per user session
- Environment variables can override sensitive paths (database location, model path)

---

### Q17: "What is WAL mode in SQLite?"

**Answer:** WAL stands for Write-Ahead Logging. In the default journal mode, SQLite locks the entire database for writes. In WAL mode, readers can continue reading while a writer is writing to a separate log file. This significantly improves concurrent performance for read-heavy applications like ours where multiple users might be viewing dashboards while others are checking in.

---

## SECTION E: Quick-Fire Answers

| Question | Short Answer |
|----------|-------------|
| What language? | Python 3.10+ |
| What database? | SQLite with WAL mode |
| How are passwords stored? | bcrypt-hashed with automatic salting |
| How many tables? | 9 tables |
| How many emotion classes? | 4 (angry, happy, neutral, sad) |
| What input size does the CNN expect? | 48×48 grayscale (1 channel) |
| How many model parameters? | 330,894 (1.26 MB) |
| What face detector? | OpenCV Haar Cascade |
| How many user roles? | 3 (admin, lecturer, student) |
| What framework? | Streamlit |
| How to run? | `streamlit run app.py` |
| Port? | localhost:8501 |
| Can you export data? | Yes, CSV export for attendance records |
| Fee currency? | LKR (Sri Lankan Rupees) |
| How are lecturers approved? | Manual admin approval via approved flag |

---

## SECTION F: Demo Script (What to Show)

### Recommended demo order (5-7 minutes):

1. **Show the landing page** — Explain the role selection system
2. **Log in as Student (John Smith)** — Show Check-In tab → capture face → show emotion detection result → save attendance
3. **Show My Attendance** — Point out the recorded check-in with emotion
4. **Show My Emotion Logs** — Show emotion history with confidence scores
5. **Show Payments** — Show fee balance and payment form
6. **Log out → Log in as Admin** — Show student management, analytics dashboard, fee management
7. **Show Interventions** — Create one and explain the workflow
8. **Show Lecturer Approvals** — Explain the approval flow
9. **Log out → Log in as Lecturer** — Show how interventions appear
10. **Show Analytics** — Attendance trends, risk distribution

### Key talking points during demo:
- "The face detection uses OpenCV's Haar Cascade classifier"
- "The emotion model is a 3-layer CNN trained on facial expression data"
- "When the admin creates an intervention, it automatically appears in the assigned lecturer's portal"
- "The system supports three roles with different access levels"
- "Passwords are bcrypt-hashed, never stored in plaintext"

---

**Good luck with the viva!**
