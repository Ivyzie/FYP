import tkinter as tk
from tkinter import messagebox
from model import screenshot, draw_boxes
import threading
import cv2

def start_anti_cheat():
    def capture_loop():
        while running:
            img_np, results = screenshot()
            img_with_boxes = draw_boxes(img_np, results)
            cv2.imshow("YOLO Detection", img_with_boxes)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    global running
    running = True
    threading.Thread(target=capture_loop).start()

def stop_anti_cheat():
    global running
    running = False
    messagebox.showinfo("Anti-Cheat", "YOLO Model stopped")

root = tk.Tk()
root.title("Anti-Cheat")

root.geometry("300x200")

label = tk.Label(root, text="Anti-Cheat")
label.pack(pady=10)

start_button = tk.Button(root, text="Start Anti-Cheat", command=start_anti_cheat)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Anti-Cheat", command=stop_anti_cheat)
stop_button.pack(pady=10)

root.mainloop()