"""Real-time face recognition and attendance marker."""

from __future__ import annotations

import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import cv2
import face_recognition
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from database.db_connection import init_db, insert_attendance  # noqa: E402

ENCODINGS_PATH = PROJECT_ROOT / "encodings" / "encodings.pkl"
TOLERANCE = 0.45


def load_encodings() -> Dict[str, List]:
    """Load known encodings from pickle file."""
    if not ENCODINGS_PATH.exists():
        raise FileNotFoundError(
            f"Encoding file not found at {ENCODINGS_PATH}. "
            "Run recognition/encode_faces.py first."
        )
    with ENCODINGS_PATH.open("rb") as fp:
        return pickle.load(fp)


def run_attendance_camera() -> None:
    """
    Main function to start the webcam, detect faces, and record attendance.
    """
    # 1. Initialize the Database
    try:
        init_db()
    except Exception as e:
        print(f"[ERROR] Could not start database: {e}")
        return

    # 2. Check if face encodings exist
    if not ENCODINGS_PATH.exists():
        print(f"[ERROR] Face data not found at: {ENCODINGS_PATH}")
        print("[HINT] Run 'python recognition/encode_faces.py' to register students first.")
        return

    # 3. Load the known faces
    try:
        encoding_data = load_encodings()
        known_encodings = encoding_data.get("encodings", [])
        known_names = encoding_data.get("names", [])
        known_rolls = encoding_data.get("rolls", ["N/A"] * len(known_names))
    except Exception as e:
        print(f"[ERROR] Failed to load student data: {e}")
        return

    if not known_encodings:
        print("[ERROR] No students are registered. Register some students first!")
        return

    # 4. Start the Webcam
    camera = cv2.VideoCapture(0)
    if not camera or not camera.isOpened():
        print("[ERROR] Webcam not found. Make sure it is plugged in.")
        return

    # To avoid marking same person multiple times in one session
    marked_students: Set[str] = set()

    print(f"[INFO] Camera started. Look into the camera to mark attendance.")
    print(f"[INFO] Press 'q' on your keyboard to stop.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                continue

            # Convert image to RGB (required by face_recognition library)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find all faces in the current frame
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Compare detected face with known student faces
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)

                name = "Unknown"
                roll = "N/A"
                if len(face_distances) > 0:
                    best_match_index = int(np.argmin(face_distances))
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                        roll = known_rolls[best_match_index]

                # Draw a box around the face
                box_color = (0, 255, 0) if name != "Unknown" else (0, 0, 255) # Green for known, Red for unknown
                cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                
                # Draw the name and roll number
                display_text = f"{name} ({roll})" if name != "Unknown" else "Unknown"
                cv2.putText(frame, display_text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

                # 5. Record Attendance in Database
                identifier = f"{roll}_{name}"
                if name != "Unknown" and identifier not in marked_students:
                    now = datetime.now()
                    insert_attendance(name, now.date(), now.time().replace(microsecond=0), roll_number=roll)
                    marked_students.add(identifier)
                    print(f"[SUCCESS] Attendance marked for: {name} ({roll})")

            # Show the video feed
            cv2.imshow("AI Attendance System", frame)
            
            # Stop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        # Cleanup
        camera.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera closed.")


if __name__ == "__main__":
    run_attendance_camera()
