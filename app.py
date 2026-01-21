"""Streamlit UI for the Smart Student Management System."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from db import (
    add_log,
    add_student,
    delete_student,
    get_logs,
    get_recent_logs,
    get_student,
    get_students,
    init_db,
    update_student,
)
from ml.model_utils import detect_primary_face, load_emotion_model, predict_emotion, preprocess_face

BASE_DIR = Path(__file__).resolve().parent
MODEL_CANDIDATES = [
    BASE_DIR / "ml" / "emotion_model.keras",
    BASE_DIR / "ml" / "emotion_model.h5",
]
NEGATIVE_EMOTIONS = {"sad", "angry", "fear", "disgust"}
RISK_WINDOW = 7


def _load_css() -> None:
    css_path = BASE_DIR / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource
def _load_model() -> Tuple[Optional[object], Optional[Path]]:
    for path in MODEL_CANDIDATES:
        if path.exists():
            return load_emotion_model(path), path
    return None, None


def _analyze_emotion(
    image: Image.Image,
    model: object,
) -> Tuple[Optional[str], Optional[float], Optional[Dict[str, float]], Optional[np.ndarray], Optional[str]]:
    rgb = image.convert("RGB")
    img_array = np.array(rgb)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    face_box = detect_primary_face(gray)
    if face_box is None:
        return None, None, None, None, "No face detected. Try a clearer frontal image."
    x, y, w, h = face_box
    face_gray = gray[y : y + h, x : x + w]
    face_tensor = preprocess_face(face_gray)
    label, confidence, prob_map = predict_emotion(model, face_tensor)
    return label, confidence, prob_map, face_gray, None


def _compute_risk(logs: List[Dict[str, Optional[str]]]) -> Tuple[str, int, int]:
    absences = sum(1 for log in logs if log.get("attendance") == "Absent")
    negative = sum(1 for log in logs if log.get("emotion") in NEGATIVE_EMOTIONS)
    if absences >= 3 and negative >= 2:
        return "High", absences, negative
    if absences >= 2 or negative >= 2:
        return "Medium", absences, negative
    return "Low", absences, negative


def _get_students_df() -> pd.DataFrame:
    students = get_students()
    return pd.DataFrame(students)


def _get_logs_df() -> pd.DataFrame:
    logs = get_logs()
    return pd.DataFrame(logs)


def main() -> None:
    st.set_page_config(
        page_title="Smart Student Management System",
        page_icon="🎓",
        layout="wide",
    )
    _load_css()
    init_db()

    model, model_path = _load_model()

    st.title("Smart Student Management System")
    st.caption(
        "Facial recognition (phase 2) + ML-based emotion detection for student retention support."
    )

    with st.sidebar:
        st.header("System Status")
        if model_path:
            st.success(f"Emotion model loaded: {model_path.name}")
        else:
            st.warning("Emotion model not found. Place it in /ml.")
        st.markdown("**Risk rules**")
        st.markdown(
            "- High: absences >= 3 AND negative emotions >= 2\n"
            "- Medium: absences >= 2 OR negative emotions >= 2\n"
            "- Low: otherwise"
        )

    tab_students, tab_attendance, tab_dashboard, tab_reports = st.tabs(
        ["Students", "Attendance + Emotion", "Dashboard", "Reports"]
    )

    with tab_students:
        st.subheader("Student Registry")
        st.write("Add, update, or remove students.")

        with st.form("add_student_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                student_id = st.text_input("Student ID *")
                batch = st.text_input("Batch")
            with col2:
                name = st.text_input("Name *")
                email = st.text_input("Email")
            with col3:
                phone = st.text_input("Phone")
            submitted = st.form_submit_button("Add Student")

        if submitted:
            if not student_id.strip() or not name.strip():
                st.error("Student ID and Name are required.")
            else:
                success, message = add_student(
                    student_id.strip(),
                    name.strip(),
                    batch.strip() or None,
                    email.strip() or None,
                    phone.strip() or None,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

        students = get_students()
        if students:
            st.markdown("#### Current Students")
            st.dataframe(pd.DataFrame(students), use_container_width=True)
        else:
            st.info("No students found. Add a student to begin.")

        st.markdown("#### Update Student")
        if students:
            selected_id = st.selectbox(
                "Select Student ID", [s["student_id"] for s in students], key="update_select"
            )
            selected_student = get_student(selected_id)
            if selected_student:
                with st.form("update_student_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        update_name = st.text_input(
                            "Name", value=selected_student["name"] or ""
                        )
                        update_batch = st.text_input(
                            "Batch", value=selected_student.get("batch") or ""
                        )
                    with col2:
                        update_email = st.text_input(
                            "Email", value=selected_student.get("email") or ""
                        )
                        update_phone = st.text_input(
                            "Phone", value=selected_student.get("phone") or ""
                        )
                    updated = st.form_submit_button("Save Changes")
                if updated:
                    if not update_name.strip():
                        st.error("Name cannot be empty.")
                    else:
                        ok = update_student(
                            selected_id,
                            update_name.strip(),
                            update_batch.strip() or None,
                            update_email.strip() or None,
                            update_phone.strip() or None,
                        )
                        if ok:
                            st.success("Student updated.")
                        else:
                            st.error("Update failed.")
        else:
            st.info("Update is disabled until students are added.")

        st.markdown("#### Delete Student")
        if students:
            delete_id = st.selectbox(
                "Select Student ID to delete", [s["student_id"] for s in students], key="delete_select"
            )
            confirm = st.checkbox("I understand this will delete the student and logs.")
            if st.button("Delete Student"):
                if not confirm:
                    st.error("Please confirm deletion.")
                else:
                    if delete_student(delete_id):
                        st.success("Student deleted.")
                    else:
                        st.error("Delete failed.")
        else:
            st.info("Delete is disabled until students are added.")

    with tab_attendance:
        st.subheader("Attendance and Emotion Logging")
        st.write("Log attendance and optionally analyze emotion from an uploaded image.")

        students = get_students()
        if not students:
            st.warning("Add at least one student before logging attendance.")
        else:
            selected_student_id = st.selectbox(
                "Student ID", [s["student_id"] for s in students], key="log_student_select"
            )
            log_date = st.date_input("Date", value=date.today())
            attendance_status = st.radio("Attendance", ["Present", "Absent"], horizontal=True)
            uploaded_file = st.file_uploader(
                "Upload face image (optional)", type=["jpg", "jpeg", "png"]
            )

            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded image", use_container_width=True)
            else:
                image = None

            col1, col2 = st.columns(2)
            with col1:
                analyze_clicked = st.button("Analyze Emotion")
            with col2:
                save_clicked = st.button("Save Log")

            if analyze_clicked:
                if not image:
                    st.error("Please upload an image first.")
                elif model is None:
                    st.error("Emotion model not available. Add /ml/emotion_model.keras.")
                else:
                    label, confidence, prob_map, face_gray, error = _analyze_emotion(image, model)
                    if error:
                        st.error(error)
                    else:
                        st.session_state["emotion_label"] = label
                        st.session_state["emotion_confidence"] = confidence
                        st.session_state["emotion_probs"] = prob_map
                        st.session_state["emotion_face"] = face_gray

            if "emotion_label" in st.session_state:
                st.markdown("**Emotion Result**")
                st.write(
                    f"Label: **{st.session_state['emotion_label']}** "
                    f"(confidence {st.session_state['emotion_confidence']:.2f})"
                )
                prob_map = st.session_state.get("emotion_probs")
                if prob_map:
                    st.bar_chart(pd.Series(prob_map).sort_values(ascending=False))
                face_gray = st.session_state.get("emotion_face")
                if face_gray is not None:
                    st.image(face_gray, caption="Detected face (grayscale)", clamp=True)

            if save_clicked:
                emotion_label = st.session_state.get("emotion_label")
                emotion_conf = st.session_state.get("emotion_confidence")
                if uploaded_file and model and not emotion_label:
                    label, confidence, _, _, error = _analyze_emotion(image, model)
                    if error:
                        st.warning(f"Emotion not saved: {error}")
                    else:
                        emotion_label = label
                        emotion_conf = confidence

                if model is None and uploaded_file:
                    st.warning("Emotion model missing. Log will be saved without emotion.")
                    emotion_label = None
                    emotion_conf = None

                add_log(
                    selected_student_id,
                    log_date.isoformat(),
                    attendance_status,
                    emotion_label,
                    emotion_conf,
                )
                st.success("Log saved.")
                st.session_state.pop("emotion_label", None)
                st.session_state.pop("emotion_confidence", None)
                st.session_state.pop("emotion_probs", None)
                st.session_state.pop("emotion_face", None)

    with tab_dashboard:
        st.subheader("Dashboard")
        students = get_students()
        logs = get_logs()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(students))
        col2.metric("Total Logs", len(logs))
        col3.metric("Model Loaded", "Yes" if model_path else "No")

        if logs:
            logs_df = pd.DataFrame(logs)
            st.markdown("#### Attendance Summary")
            attendance_counts = logs_df["attendance"].value_counts()
            st.bar_chart(attendance_counts)

            st.markdown("#### Emotion Distribution")
            emotion_df = logs_df[logs_df["emotion"].notna() & (logs_df["emotion"] != "")]
            if not emotion_df.empty:
                st.bar_chart(emotion_df["emotion"].value_counts())
            else:
                st.info("No emotion logs yet.")

            st.markdown("#### Risk Overview")
            risk_rows = []
            for student in students:
                recent = get_recent_logs(student["student_id"], limit=RISK_WINDOW)
                risk, absences, negative = _compute_risk(recent)
                risk_rows.append(
                    {
                        "student_id": student["student_id"],
                        "name": student["name"],
                        "risk": risk,
                        "recent_absences": absences,
                        "recent_negative_emotions": negative,
                    }
                )
            risk_df = pd.DataFrame(risk_rows)
            risk_counts = risk_df["risk"].value_counts().reindex(
                ["High", "Medium", "Low"], fill_value=0
            )
            st.bar_chart(risk_counts)
            st.dataframe(risk_df, use_container_width=True)

            st.markdown("#### Logs Table")
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No logs yet. Add attendance and emotion entries.")

    with tab_reports:
        st.subheader("Reports and Export")
        students_df = _get_students_df()
        logs_df = _get_logs_df()

        if not students_df.empty:
            st.download_button(
                "Download Students CSV",
                data=students_df.to_csv(index=False).encode("utf-8"),
                file_name="students.csv",
                mime="text/csv",
            )
        else:
            st.info("No students to export.")

        if not logs_df.empty:
            st.download_button(
                "Download Logs CSV",
                data=logs_df.to_csv(index=False).encode("utf-8"),
                file_name="logs.csv",
                mime="text/csv",
            )
        else:
            st.info("No logs to export.")


if __name__ == "__main__":
    main()
