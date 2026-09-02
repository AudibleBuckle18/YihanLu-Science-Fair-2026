from ultralytics import YOLO

# 1. Load your custom trained brain
model = YOLO('runs/detect/new_sorter-2/weights/best.pt')

# 2. Turn on the webcam (source='0') and look for VEX parts!
# conf=0.6 means it will only draw a box if it is 60% confident
results = model.predict(source='0', show=True, conf=0.6)

 