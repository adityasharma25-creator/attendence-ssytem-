"""
-------------------------------------------------------------------------
AI FACE RECOGNITION ATTENDANCE SYSTEM - ALL-IN-ONE STARTER
-------------------------------------------------------------------------
This script is a simple menu that helps you run the different parts of 
your project without typing complex commands.
"""

import os
import subprocess
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_dashboard():
    print("\n[INFO] Starting the Analytics Dashboard...")
    print("[HINT] A new window should open in your browser soon.\n")
    try:
        # Run streamlit as a subprocess
        subprocess.run(["streamlit", "run", "dashboard/dashboard.py"])
    except KeyboardInterrupt:
        print("\n[INFO] Dashboard stopped.")

def run_camera():
    print("\n[INFO] Starting the AI Attendance Camera...")
    print("[HINT] Press 'q' on your keyboard when you want to stop the camera.\n")
    try:
        # Run the attendance marking script
        subprocess.run([sys.executable, "attendance/mark_attendance.py"])
    except KeyboardInterrupt:
        print("\n[INFO] Camera stopped.")

def main_menu():
    while True:
        clear_screen()
        print("====================================================")
        print("   WELCOME TO YOUR AI ATTENDANCE SYSTEM")
        print("====================================================")
        print("   Please select an option:")
        print("   1. Run Camera (Mark Attendance)")
        print("   2. Run Dashboard (Add Students & View Logs)")
        print("   3. Exit")
        print("====================================================")
        
        choice = input("Enter your choice (1, 2, or 3): ")
        
        if choice == '1':
            run_camera()
            input("\nPress Enter to return to menu...")
        elif choice == '2':
            run_dashboard()
            input("\nPress Enter to return to menu...")
        elif choice == '3':
            print("\nGoodbye! See you again soon.")
            break
        else:
            print("\n[ERROR] Invalid choice. Please enter 1, 2, or 3.")
            input("Press Enter to try again...")

if __name__ == "__main__":
    main_menu()
