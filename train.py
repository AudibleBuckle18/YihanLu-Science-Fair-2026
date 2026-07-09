from ultralytics import YOLO

# Load the base nano model
model = YOLO('yolov8n.pt')

# Train the model on your custom dataset
# Make sure the folder name matches exactly what you named it!
results = model.train(
    data='Data2/data.yaml',
    epochs=50,          # 50 passes over the dataset
    imgsz=640,          # Standard image size
    batch=16,           # Processes 16 images at a time
    device='mps',       # Forces Apple Silicon GPU acceleration
    name='vex_sorter'   # The folder where it will save the final weights
)