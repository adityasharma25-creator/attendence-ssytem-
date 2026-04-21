"""Generate face encodings from dataset/student_images."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Tuple

import face_recognition


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "dataset" / "student_images"
ENCODINGS_PATH = PROJECT_ROOT / "encodings" / "encodings.pkl"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_images_and_metadata() -> List[dict]:
    """Load dataset file paths and student metadata from filenames."""
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATASET_DIR}")

    image_files = sorted([p for p in DATASET_DIR.iterdir() if p.suffix.lower() in VALID_EXTENSIONS])
    if not image_files:
        raise FileNotFoundError(f"No image files found in {DATASET_DIR}")

    records: List[dict] = []
    for image_path in image_files:
        stem = image_path.stem
        # Format: rollNumber_Name (e.g. 101_John_Doe) or just Name
        parts = stem.split("_", 1)
        if len(parts) == 2 and parts[0].isalnum():
            roll_no = parts[0]
            name = parts[1].replace("_", " ").strip()
        else:
            roll_no = "N/A"
            name = stem.replace("_", " ").strip()

        if name:
            records.append({
                "path": image_path,
                "name": name,
                "roll_number": roll_no
            })
    return records


def encode_faces() -> None:
    """Generate and save known face encodings."""
    known_encodings = []
    known_names = []
    known_rolls = []

    for record in load_images_and_metadata():
        image_path = record["path"]
        name = record["name"]
        roll_no = record["roll_number"]

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if not encodings:
            print(f"[WARN] No face found in image: {image_path.name}")
            continue
        if len(encodings) > 1:
            print(f"[WARN] Multiple faces found in {image_path.name}; using first face.")

        known_encodings.append(encodings[0])
        known_names.append(name)
        known_rolls.append(roll_no)
        print(f"[OK] Encoded: {name} ({roll_no})")

    if not known_encodings:
        raise RuntimeError("No valid face encodings generated. Check your dataset images.")

    ENCODINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ENCODINGS_PATH.open("wb") as fp:
        pickle.dump({
            "encodings": known_encodings,
            "names": known_names,
            "rolls": known_rolls
        }, fp)

    print(f"[DONE] Saved {len(known_encodings)} face encodings to {ENCODINGS_PATH}")


if __name__ == "__main__":
    encode_faces()
