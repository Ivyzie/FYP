from inference import InferencePipeline
from inference.core.interfaces.camera.entities import VideoFrame
import cv2
import supervision as sv
import mss
import numpy as np

# Create annotators
label_annotator = sv.LabelAnnotator()
box_annotator = sv.BoxAnnotator()

def my_custom_sink(predictions: dict, video_frame: VideoFrame):
    labels = [p["class"] for p in predictions["predictions"]]
    detections = sv.Detections.from_inference(predictions)
    image = label_annotator.annotate(
        scene=video_frame.image.copy(), detections=detections, labels=labels
    )
    image = box_annotator.annotate(image, detections=detections)
    cv2.imshow("Predictions", image)
    cv2.waitKey(1)

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # First monitor
        while True:
            img = sct.grab(monitor)
            img_np = np.array(img)
            yield img_np

pipeline = InferencePipeline.init(
    model_id="yolov8x-1280",
    video_reference=capture_screen(),  # Use screen capture generator
    on_prediction=my_custom_sink,
    providers=["cuda", "cpu"],
)

def start_pipeline():
    pipeline.start()

def stop_pipeline():
    pipeline.join()

# async def screenshot(frame=None):
#     # Capture screenshot
#     with mss.mss() as sct:
#         monitor = sct.monitors[1]  # Primary monitor
#         img = sct.grab(monitor)
#         img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
#         img_np = np.array(img)
    
#     # Ensure the image is float32
#     img_np = img_np.astype(np.float32)
    
#     # Convert image to list for JSON serialization
#     img_list = img_np.tolist()
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.post("http://localhost:9001/", json={"image": img_list}) as response:
#                 if response.status == 200:
#                     results = await response.json()
#                 else:
#                     print(f"Error: Server returned status {response.status}")
#                     results = []
#     except Exception as e:
#         print(f"Error connecting to server: {e}")
#         results = []
    
#     return img_np, results

# def draw_boxes(img, results):
#     for result in results:
#         for box in result.boxes:
#             # Ensure box.xyxy is a list or array of coordinates
#             x1, y1, x2, y2 = map(int, box.xyxy[0])  # Access the first element if it's a list of lists
#             class_name = result.names[int(box.cls)]
#             confidence = box.conf[0]  # Access the first element if it's a list
#             label = f"{class_name} ({confidence:.2f})"
#             cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#     return img