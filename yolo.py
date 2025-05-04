import os
import time
import json
import csv
import threading
from collections import deque
from queue import Queue, Empty

import numpy as np
import cv2
import importlib.util
import mss
import psutil
import sys
from pymem import Pymem
import pymem.process
from ultralytics import YOLO

# ——— CONFIGURATION ———
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OFFSETS_FILE       = os.path.join(BASE_DIR, "cheat", "Python-CSGO-Cheat", "offsets", "offsets.json")
OFFSETS_PY         = os.path.join(BASE_DIR, "Offsets.py")
MODEL_PATH         = os.path.join(BASE_DIR, "best.pt")

# SNAP THRESHOLDS
LOCK_ANGLE_THRESH  = 3.0     # degrees for snap detection
SMALL_DELTA_THRESH = 0.3     # ignore very small movements
SNAP_COUNT         = 2       # require 2 snaps to flag
SNAP_WINDOW        = 1.5     # seconds window
SNAP_DEBOUNCE      = 0.2     # min seconds between snaps

# LOCK DETECTION (head point)
LOCK_DIST_THRESH   = 10      # pixels from center for lock detection
LOCK_COUNT         = 1       # require 1 lock event
LOCK_WINDOW        = 1.0     # seconds window
LOCK_DEBOUNCE      = 0.1     # debounce for lock detection

CHEAT_BORDER_DURATION = 3.0  # seconds red border remains
FRAME_QUEUE_SIZE      = 5
MONITOR               = {'top':0, 'left':0, 'width':1920, 'height':1080}
CSV_PATH              = 'features.csv'

# ——— LOAD YOLO MODEL ———
model = YOLO(MODEL_PATH)

# ——— LOAD OFFSETS ———
with open(OFFSETS_FILE, 'r') as f:
    offsets = json.load(f)
netvars = offsets['netvars']

spec = importlib.util.spec_from_file_location("Offsets", OFFSETS_PY)
Offsets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Offsets)

# ——— PRE-FLIGHT CHECK ———
if not any(proc.name().lower() == "csgo.exe" for proc in psutil.process_iter()):
    print("[ERROR] csgo.exe not found. Please launch CS:GO first.")
    sys.exit(1)

# ——— INIT PROCESS ———
pm = Pymem('csgo.exe')
client_mod = pymem.process.module_from_name(pm.process_handle, 'client.dll')
client_base = client_mod.lpBaseOfDll

def _sig_to_int(raw):
    s = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else str(raw)
    return int(s, 0)

raw_local = Offsets.get_sig(pm, 'client.dll',
    bytes(Offsets.PatternDict['dwLocalPlayer'], 'raw_unicode_escape'), extra=4, offset=3)
raw_list  = Offsets.get_sig(pm, 'client.dll',
    bytes(Offsets.PatternDict['dwEntityList'], 'raw_unicode_escape'), extra=0, offset=0)

dwLocalPlayerAddr = _sig_to_int(raw_local) + client_base
entity_list_offset = _sig_to_int(raw_list)
entity_list_addr   = client_base + entity_list_offset

# ——— CSV LOGGER ———
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)
csv_file   = open(CSV_PATH, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['frame','timestamp','angle_delta','snap_count','lock_count','flag'])

# ——— CAPTURE THREAD ———
frame_q = Queue(maxsize=FRAME_QUEUE_SIZE)
def cap_loop(q):
    sct = mss.mss()
    while True:
        q.put(np.array(sct.grab(MONITOR)))
threading.Thread(target=cap_loop, args=(frame_q,), daemon=True).start()

# ——— STATE ———
view_times      = deque()
lock_times      = deque()
prev_ang        = None
prev_dang       = 0.0
prev_snap_time  = 0.0
prev_lock_time  = 0.0
frame_idx       = 0
last_flag_time  = 0.0

# ——— INIT ANGLES ———
try:
    lp = pm.read_uint(dwLocalPlayerAddr)
    prev_ang = np.array([
        pm.read_float(lp + netvars['m_angEyeAnglesX']),
        pm.read_float(lp + netvars['m_angEyeAnglesY'])
    ])
except Exception as e:
    print(f"[DEBUG] Angle init failed: {e}")

# ——— MAIN LOOP ———
try:
    while True:
        try:
            raw = frame_q.get(timeout=0.5)
        except Empty:
            continue

        frame = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        h, w = frame.shape[:2]
        now = time.time()

        # 1) Read & compute view angle delta
        curr_ang = None
        try:
            lp = pm.read_uint(dwLocalPlayerAddr)
            curr_ang = np.array([
                pm.read_float(lp + netvars['m_angEyeAnglesX']),
                pm.read_float(lp + netvars['m_angEyeAnglesY'])
            ])
        except:
            pass

        if curr_ang is not None and prev_ang is not None:
            diff = curr_ang - prev_ang
            if diff[1] > 180:  diff[1] -= 360
            if diff[1] < -180: diff[1] += 360
            angle_delta = float(np.linalg.norm(diff))
            prev_ang = curr_ang
        else:
            angle_delta = 0.0

        # 2) SNAP detection (edge + debounce)
        view_times = deque(t for t in view_times if now - t <= SNAP_WINDOW)
        if (prev_dang <= SMALL_DELTA_THRESH
            and angle_delta > LOCK_ANGLE_THRESH
            and now - prev_snap_time > SNAP_DEBOUNCE):
            view_times.append(now)
            prev_snap_time = now
            print(f"[DEBUG] Snap @ {now:.2f}s Δ={angle_delta:.1f}")
        prev_dang = angle_delta

        # 3) YOLO + lock detection on head point
        results = model(frame)[0]
        locked_this_frame = False
        for box in results.boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = box.astype(int)
            # draw body box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

            # compute head point at top 15% of box
            box_h = y2 - y1
            head_x = (x1 + x2) // 2
            head_y = y1 + int(box_h * 0.15)
            cv2.circle(frame, (head_x, head_y), 4, (255,0,0), -1)

            # record one lock per frame
            if (not locked_this_frame
                and abs(head_x - w//2) < LOCK_DIST_THRESH
                and abs(head_y - h//2) < LOCK_DIST_THRESH
                and now - prev_lock_time > LOCK_DEBOUNCE):
                lock_times.append(now)
                prev_lock_time = now
                locked_this_frame = True

        lock_times = deque(t for t in lock_times if now - t <= LOCK_WINDOW)

        # 4) Flag logic
        snap_ok = len(view_times) >= SNAP_COUNT
        lock_ok = len(lock_times) >= LOCK_COUNT
        flag    = snap_ok and lock_ok
        if flag:
            last_flag_time = now

        # 5) Overlay & logging
        color = (0,0,255) if now - last_flag_time <= CHEAT_BORDER_DURATION else (0,255,0)
        cv2.rectangle(frame, (0,0), (w-1,h-1), color, 4)
        status = f"Δ:{angle_delta:.1f}° Snaps:{len(view_times)} Locks:{len(lock_times)}"
        cv2.putText(frame, status, (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        if flag:
            cv2.putText(frame, "CHEAT", (10,60),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0,0,255), 3)

        csv_writer.writerow([frame_idx, now, f"{angle_delta:.1f}",
                             len(view_times), len(lock_times), flag])
        csv_file.flush()

        # 6) Display
        cv2.imshow('AntiCheat', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_idx += 1

finally:
    csv_file.close()
    cv2.destroyAllWindows()
