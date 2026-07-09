import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt') # set the YOLO model weights to default weights included 
cap = cv2.VideoCapture(0)

print("Attempting to connect to camera...")

while cap.isOpened():
    success, frame = cap.read()
    
    if not success:
        print("Camera is connected, but refusing to send video frames!")
        break

    print("Got a frame. Running YOLO")
    results = model(frame)
    annotated_frame = results[0].plot()

    print("🖼️ Attempting to draw the window...")
    cv2.imshow("YOLOv8 VEX Sorter Vision", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

