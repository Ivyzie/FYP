from ultralytics import YOLO
import mss
import numpy as np
from PIL import Image
import cv2

model = YOLO("yolo11n.pt")

def screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        img_np = np.array(img)
        results = model.predict(img_np)
        return img_np, results

def draw_boxes(img, results):
    for result in results:
        for box in result.boxes:
            # Ensure box.xyxy is a list or array of coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Access the first element if it's a list of lists
            class_name = result.names[int(box.cls)]
            confidence = box.conf[0]  # Access the first element if it's a list
            label = f"{class_name} ({confidence:.2f})"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return img