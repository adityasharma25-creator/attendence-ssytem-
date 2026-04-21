# AI Face Recognition Attendance System with Cloud MySQL and Dashboard

Production-ready face recognition attendance project using Python, OpenCV, `face_recognition`, MySQL, and Streamlit.

## Features

- Real-time face detection and recognition from webcam
- Student registration by image filename (`student_name.jpg`)
- Face embedding generation and pickle persistence
- Attendance storage in cloud/local MySQL
- Duplicate prevention within the same camera session
- Configurable recognition threshold (`TOLERANCE`)
- Streamlit dashboard with:
  - attendance table
  - total attendance and unique student metrics
  - attendance per student chart
  - daily attendance trend
  - name-based search filter
  - near real-time refresh

## Project Structure

```text
face-recognition-attendance-system
│
├── dataset/
│   └── student_images/
│
├── encodings/
│   └── encodings.pkl
│
├── database/
│   ├── db_connection.py
│   └── schema.sql
│
├── attendance/
│   └── mark_attendance.py
│
├── recognition/
│   └── encode_faces.py
│
├── dashboard/
│   └── dashboard.py
│
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- Webcam
- MySQL server (cloud or local)
- OS support: Windows/Linux

## 1) Installation

```bash
pip install -r requirements.txt
```

## 2) Configure Cloud MySQL

Set these environment variables before running the app:

- `DB_HOST`
- `DB_PORT` (default `3306`)
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME` (default `attendance_ai`)

### Windows PowerShell Example

```powershell
$env:DB_HOST="your-cloud-host"
$env:DB_PORT="3306"
$env:DB_USER="your-user"
$env:DB_PASSWORD="your-password"
$env:DB_NAME="attendance_ai"
```

### Linux/macOS Example

```bash
export DB_HOST="your-cloud-host"
export DB_PORT="3306"
export DB_USER="your-user"
export DB_PASSWORD="your-password"
export DB_NAME="attendance_ai"
```

## 3) Create Database Schema

Run SQL from `database/schema.sql`:

```sql
CREATE DATABASE IF NOT EXISTS attendance_ai;

USE attendance_ai;

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name_date (name, date),
    INDEX idx_date (date)
);
```

## 4) Add Student Images

Place student face images in:

`dataset/student_images/`

Use filename pattern:

- `john_doe.jpg`
- `alice.png`

Names are automatically parsed from filenames.

## 5) Generate Face Encodings

```bash
python recognition/encode_faces.py
```

This creates:

`encodings/encodings.pkl`

## 6) Start Face Recognition Attendance Camera

```bash
python attendance/mark_attendance.py
```

- Press `q` to stop camera.
- Recognized faces are marked once per session.
- Attendance is inserted into MySQL with timestamp.

## 7) Launch Streamlit Dashboard

```bash
streamlit run dashboard/dashboard.py
```

## Notes for Production

- Use strong DB credentials and network allow-listing/IP restrictions.
- Prefer SSL-enabled MySQL connections if your provider supports it.
- Store secrets in environment variables or secret manager (not in code).
- You can schedule periodic backups for attendance table.

## Troubleshooting

- If webcam fails, verify camera permissions and device availability.
- If recognition is weak, adjust `TOLERANCE` in `attendance/mark_attendance.py`.
- If DB fails, re-check environment variables and firewall access.
"# attendence-ssytem-" 
