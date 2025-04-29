from ultralytics import YOLO
import cv2
import numpy as np
import mss
import time

model = YOLO("best.pt")

monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}

sct = mss.mss()

while True:
    start_time = time.time()

    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    results = model.predict(frame, imgsz = 640, conf=0.5)

    for r in results :
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            cls = int(box.cls[0])
            conf = box.conf[0]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{model.names[cls]} {conf:.2f}" if hasattr(model, "names") else f"Class {cls} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    fps = 1 / (time.time() - start_time)
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imshow("AntiCheat", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()