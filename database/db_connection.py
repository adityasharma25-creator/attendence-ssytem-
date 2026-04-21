"""Database utilities for attendance system.

Uses environment variables for cloud MySQL configuration:
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
Falls back to SQLite if MySQL is unavailable.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import date, time
from pathlib import Path
from typing import Dict, List, Optional, Union

import mysql.connector
from mysql.connector import Error

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQLITE_PATH = PROJECT_ROOT / "database" / "attendance_ai.db"


def _get_db_type() -> str:
    """Return 'mysql' if DB_HOST is set, else 'sqlite'."""
    return "mysql" if os.getenv("DB_HOST") else "sqlite"


def connect_db() -> Union[mysql.connector.MySQLConnection, sqlite3.Connection]:
    """Create and return a database connection (MySQL or SQLite)."""
    if _get_db_type() == "mysql":
        try:
            config = {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT", "3306")),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "attendance_ai"),
                "autocommit": True,
            }
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                return connection
        except Error as exc:
            print(f"[WARN] MySQL connection failed: {exc}. Falling back to SQLite.")

    # Fallback to SQLite
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Creates the necessary database tables (students and attendance) if they don't exist.
    This is called automatically when the system starts.
    """
    db_type = _get_db_type()
    
    # SQLite uses AUTOINCREMENT, MySQL uses AUTO_INCREMENT
    auto_inc_logic = "AUTOINCREMENT" if db_type == "sqlite" else "AUTO_INCREMENT"
    
    create_students_table = """
    CREATE TABLE IF NOT EXISTS students (
        roll_number VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_attendance_table = f"""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY {auto_inc_logic},
        name VARCHAR(100) NOT NULL,
        roll_number VARCHAR(50),
        date DATE NOT NULL,
        time TIME NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    idx1 = "CREATE INDEX IF NOT EXISTS idx_name_date ON attendance (name, date);"
    idx2 = "CREATE INDEX IF NOT EXISTS idx_date ON attendance (date);"
    idx3 = "CREATE INDEX IF NOT EXISTS idx_roll ON attendance (roll_number);"

    try:
        with closing(connect_db()) as connection:
            cursor = connection.cursor()
            cursor.execute(create_students_table)
            cursor.execute(create_attendance_table)
            
            # Migration: Ensure roll_number exists in attendance
            try:
                cursor.execute("ALTER TABLE attendance ADD COLUMN roll_number VARCHAR(50);")
            except Exception:
                pass # Column already exists
            
            # Indexes for faster searching
            if db_type == "sqlite":
                cursor.execute(idx1)
                cursor.execute(idx2)
                cursor.execute(idx3)
                
            connection.commit()
            print(f"[INFO] Database initialized ({db_type}).")
    except Exception as e:
        print(f"[ERROR] Database init failed: {e}")


def register_student(roll_number: str, name: str) -> bool:
    """
    Saves a new student's info (Roll No and Name) into the database.
    """
    placeholder = "%s" if _get_db_type() == "mysql" else "?"
    query = f"INSERT INTO students (roll_number, name) VALUES ({placeholder}, {placeholder})"
    try:
        with closing(connect_db()) as connection:
            cursor = connection.cursor()
            cursor.execute(query, (roll_number, name))
            connection.commit()
            return True
    except Exception as e:
        print(f"[ERROR] Student registration failed: {e}")
        return False


def fetch_all_students() -> List[Dict[str, object]]:
    """
    Retrieves all registered students from the database.
    """
    query = "SELECT roll_number, name, created_at FROM students ORDER BY name ASC"
    try:
        with closing(connect_db()) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            if _get_db_type() == "mysql":
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[ERROR] Fetching students failed: {e}")
        return []


def insert_attendance(student_name: str, att_date: date, att_time: time, roll_number: Optional[str] = None) -> None:
    """
    Records a student's presence with date and time.
    """
    placeholder = "%s" if _get_db_type() == "mysql" else "?"
    insert_query = f"""
    INSERT INTO attendance (name, roll_number, date, time) 
    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
    """

    try:
        with closing(connect_db()) as connection:
            cursor = connection.cursor()
            cursor.execute(insert_query, (student_name, roll_number, str(att_date), str(att_time)))
            connection.commit()
    except Exception as e:
        print(f"[ERROR] Failed to insert attendance: {e}")


def fetch_all_attendance() -> List[Dict[str, object]]:
    """
    Retrieves all attendance logs from the database, newest first.
    """
    query = "SELECT id, name, roll_number, date, time, created_at FROM attendance ORDER BY id DESC"
    try:
        with closing(connect_db()) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            if _get_db_type() == "mysql":
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                return [dict(row) for row in rows]
    except Exception as e:
        print(f"[ERROR] Fetching attendance failed: {e}")
        return []


def export_attendance_to_excel(file_path: Optional[str] = None) -> str:
    """
    Exports all attendance records to an Excel file (.xlsx).
    Returns the path to the saved file.
    """
    import pandas as pd
    from datetime import datetime
    
    records = fetch_all_attendance()
    if not records:
        return "No records found to export."
        
    df = pd.DataFrame(records)
    
    # Generate default filename if not provided
    if not file_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"attendance_report_{timestamp}.xlsx"
    
    try:
        df.to_excel(file_path, index=False)
        print(f"[INFO] Attendance exported to: {file_path}")
        return file_path
    except Exception as e:
        print(f"[ERROR] Excel export failed: {e}")
        return f"Export failed: {e}"
