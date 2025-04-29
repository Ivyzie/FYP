import tkinter as tk
from tkinter import messagebox
from model import start_pipeline, stop_pipeline
import cv2
import asyncio
import threading

from model import start_pipeline, stop_pipeline

def start_anti_cheat():
    global running
    running = True
    start_pipeline()

def stop_anti_cheat():
    global running
    running = False
    stop_pipeline()
    messagebox.showinfo("Anti-Cheat", "YOLO Model stopped")