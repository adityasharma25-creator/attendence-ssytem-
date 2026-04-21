import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from database.db_connection import (
    fetch_all_attendance, 
    init_db, 
    register_student, 
    fetch_all_students,
    export_attendance_to_excel
)  # noqa: E402
from recognition.encode_faces import encode_faces  # noqa: E402

@st.cache_data(ttl=5)
def load_attendance_data() -> pd.DataFrame:
    """Fetch attendance data from the database."""
    records = fetch_all_attendance()
    if not records:
        return pd.DataFrame(columns=["id", "name", "roll_number", "date", "time", "created_at"])
    return pd.DataFrame(records)


@st.cache_data(ttl=1)
def load_student_data() -> pd.DataFrame:
    """Fetch registered students."""
    records = fetch_all_students()
    if not records:
        return pd.DataFrame(columns=["roll_number", "name", "created_at"])
    return pd.DataFrame(records)


def main() -> None:
    st.set_page_config(page_title="AI Attendance Dashboard", layout="wide", page_icon="📊")
    st.title("🚀 AI Face Recognition Attendance Dashboard")

    db_type = "MySQL Cloud" if os.getenv("DB_HOST") else "SQLite Local"
    st.sidebar.info(f"**Database:** {db_type}")

    try:
        init_db()
    except Exception as exc:
        st.error(f"Failed to connect to database: {exc}")
        return

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Attendance Log", "📈 Analytics", "👤 Student Management", "💡 Help Guide"])

    with tab1:
        df = load_attendance_data()
        
        # --- Excel Export Button ---
        col1, col2 = st.columns([8, 2])
        with col2:
            if not df.empty:
                if st.button("📊 Export to Excel"):
                    file_path = export_attendance_to_excel()
                    st.success(f"Saved: {file_path}")
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="Download File",
                            data=f,
                            file_name=file_path,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

        if df.empty:
            st.warning("No attendance records found yet.")
        else:
            st.sidebar.header("Filters")
            search_name = st.sidebar.text_input("Search student", placeholder="Name or Roll Number")
            
            if search_name:
                filtered_df = df[
                    (df["name"].str.contains(search_name, case=False, na=False)) |
                    (df["roll_number"].astype(str).str.contains(search_name, case=False, na=False))
                ].copy()
            else:
                filtered_df = df.copy()

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Records", len(filtered_df))
            m2.metric("Unique Students", filtered_df["name"].nunique())
            
            # Simple today logic
            today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
            today_count = len(filtered_df[filtered_df["date"].astype(str) == today_str])
            m3.metric("Attendance Today", today_count)

            st.subheader("Recent Attendance")
            st.dataframe(filtered_df, use_container_width=True)

    with tab2:
        if not df.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Attendance Per Student")
                st.bar_chart(df["name"].value_counts())
            with col_b:
                st.subheader("Daily Trend")
                daily_counts = df.groupby("date").size()
                st.line_chart(daily_counts)
        else:
            st.info("No data available for analytics.")

    with tab3:
        sub_tab_list = ["Register New Student", "Registered Students"]
        c1, c2 = st.tabs(sub_tab_list)

        with c1:
            st.subheader("Add New Student")
            st.info("Fill the form below and upload a clear photo of the student's face.")
            with st.form("registration_form", clear_on_submit=True):
                roll_no = st.text_input("Roll Number", placeholder="e.g. 101")
                full_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                uploaded_file = st.file_uploader("Upload Student Photo", type=["jpg", "jpeg", "png"])
                submit_btn = st.form_submit_button("Register Student")

                if submit_btn:
                    if not roll_no or not full_name or not uploaded_file:
                        st.error("Please provide all details (Roll Number, Name, and Photo).")
                    else:
                        # Save Image
                        img_dir = PROJECT_ROOT / "dataset" / "student_images"
                        img_dir.mkdir(parents=True, exist_ok=True)
                        file_ext = uploaded_file.name.split(".")[-1]
                        # Safe naming: roll_name.ext
                        clean_name = full_name.replace(" ", "_")
                        file_name = f"{roll_no}_{clean_name}.{file_ext}"
                        img_path = img_dir / file_name

                        with open(img_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Register in DB
                        if register_student(roll_no, full_name):
                            st.success(f"Successfully registered {full_name} ({roll_no})!")
                            st.warning("⚠️ AI updating required! Click the button below.")
                            load_student_data.clear()
                        else:
                            st.error("Database registration failed. Check if roll number is duplicate.")

            st.divider()
            st.subheader("Face Encodings")
            st.write("Click this button whenever you add a new student so the AI can learn their face.")
            if st.button("🔄 Update AI Brain (Face Encodings)"):
                with st.spinner("Generating encodings..."):
                    try:
                        encode_faces()
                        st.success("AI updated successfully! You can now start the camera.")
                    except Exception as e:
                        st.error(f"Encoding failed: {e}")

        with c2:
            st.subheader("Student Directory")
            student_df = load_student_data()
            st.dataframe(student_df, use_container_width=True)
            if st.button("Refresh List"):
                load_student_data.clear()
                st.rerun()

    with tab4:
        st.subheader("📖 Getting Started Guide")
        st.markdown("""
        ### How to use this system:
        
        1.  **Register Students**: Go to the **Student Management** tab. Enter the student's roll number, name, and upload a clear photo of their face.
        2.  **Update AI Brain**: After adding students, scroll down in the **Student Management** tab and click **Update AI Brain**. This tells the AI what the new students looks like.
        3.  **Start Attendance**: Run the `main.py` script and select **Camera** (or run `attendance/mark_attendance.py`).
        4.  **Save to Excel**: Go to the **Attendance Log** tab and click **Export to Excel** to save your records!
        
        *Tip: Make sure the room has good lighting for the best results!*
        """)

    if st.sidebar.button("Manual Refresh All"):
        load_attendance_data.clear()
        load_student_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
