from ultralytics import YOLO

# Load the base nano model
model = YOLO('yolov8n.pt')

# Make sure the folder name matches exactly!
results = model.train(
    data='Data3/data.yaml',
    epochs=100,          # 50 passes over the dataset
    imgsz=640,          # Standard image size
    batch=16,           # Processes 16 images at a time
    device='mps',       # Apple Silicon GPU acceleration
    name='new_sorter'   # The folder where it will save the final weights
)

