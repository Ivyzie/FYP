import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import sys
import os
import random
import cv2
import csv

process = None
VIDEO_FOLDER = "videos"
skip_event = threading.Event()
CHOICES_CSV = "choices.csv"

# Ensure choices.csv exists with header
if not os.path.exists(CHOICES_CSV):
    with open(CHOICES_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["clip", "feedback"])

# --- Anti-Cheat Controls ---
def start_anti_cheat():
    global process
    if process is None:
        try:
            process = subprocess.Popen([sys.executable, "yolo.py"])
            status_var.set("Status: Running")
            messagebox.showinfo("Anti-Cheat", "YOLO Model started")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start YOLO: {e}")


def stop_anti_cheat():
    global process
    if process:
        try:
            process.terminate()
            process = None
            status_var.set("Status: Idle")
            messagebox.showinfo("Anti-Cheat", "YOLO Model stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop YOLO: {e}")

# --- Video Playback & Feedback ---
def play_random_clip():
    clips = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith((".mp4", ".avi", ".mkv"))]
    if not clips:
        messagebox.showwarning("No Clips", "No video found in videos folder.")
        return

    clip = random.choice(clips)
    clip_path = os.path.join(VIDEO_FOLDER, clip)
    status_var.set(f"Playing: {clip}")
    skip_event.clear()

    cap = cv2.VideoCapture(clip_path)
    while cap.isOpened():
        if skip_event.is_set():
            break
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Clip Playback", frame)
        if cv2.waitKey(30) & 0xFF in (ord('q'), 27):
            break
    cap.release()
    cv2.destroyWindow("Clip Playback")

    # Feedback prompt loop
    while True:
        resp = messagebox.askquestion(
            "Feedback",
            "Is this player cheating?",
            icon='question',
            type='yesnocancel'
        )
        if resp == 'yes':
            feedback = "Cheater"
            break
        elif resp == 'no':
            feedback = "Legit"
            break
        else:
            # Replay
            play_same_clip(clip_path)
            continue

    messagebox.showinfo("Your Feedback", f"You marked: {feedback}")
    status_var.set("Status: Idle")

    # Log feedback to CSV (append only)
    with open(CHOICES_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([clip, feedback])


def play_same_clip(path):
    skip_event.clear()
    cap = cv2.VideoCapture(path)
    while cap.isOpened():
        if skip_event.is_set():
            break
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Clip Playback", frame)
        if cv2.waitKey(30) & 0xFF in (ord('q'), 27):
            break
    cap.release()
    cv2.destroyWindow("Clip Playback")


def skip_clip():
    skip_event.set()

# --- GUI Setup ---
def build_gui():
    global status_var

    root = tk.Tk()
    root.title("Anti-Cheat Controller")
    root.geometry("380x300")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TButton', font=('Segoe UI', 10), padding=6)
    style.configure('TLabel', font=('Segoe UI', 11))

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)

    ttk.Label(frame, text="CS:GO Anti-Cheat", font=('Segoe UI', 14, 'bold')).pack(pady=(0,10))

    # Control buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Start Anti-Cheat", width=18,
               command=lambda: threading.Thread(target=start_anti_cheat, daemon=True).start()
    ).grid(row=0, column=0, padx=5)

    ttk.Button(btn_frame, text="Stop Anti-Cheat", width=18,
               command=lambda: threading.Thread(target=stop_anti_cheat, daemon=True).start()
    ).grid(row=0, column=1, padx=5)

    ttk.Button(frame, text="Are they cheating? Help us decide.", width=43,
               command=lambda: threading.Thread(target=play_random_clip, daemon=True).start()
    ).pack(pady=(10,5))

    # Skip button below play random clip
    ttk.Button(frame, text="Skip Clip", width=43,
               command=skip_clip
    ).pack(pady=(0,10))

    status_var = tk.StringVar(value="Status: Idle")
    ttk.Label(frame, textvariable=status_var).pack(pady=(10,0))

    def on_close():
        if process:
            process.terminate()
        skip_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == '__main__':
    build_gui()
