import cv2
import os
import time

# IMPORTANT!!! CHANGE NAME OF ITEM
part_name = "newdata" 

# make a folder (or if the foler already exists, save to that folder)
save_dir = "new_testset"
os.makedirs(save_dir, exist_ok=True)

# Connect to your locked-in USB camera
cap = cv2.VideoCapture(0) # index the camera correct;y
img_count = 0

print("Data Collector Armed")
print("Press 's' to SNAP a photo.")
print("Press 'q' to QUIT.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame.")
        break

    # Show the live feed in a window
    cv2.imshow("VEX Data Collector", frame)

    # Wait for a key press
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        # save the keyframe as a png
        img_name = os.path.join(save_dir, f"{part_name}_{int(time.time())}.png")
        cv2.imwrite(img_name, frame)
        print(f"Saved: {img_name}")
        img_count += 1
        #quit the program if commanded to
    elif key == ord('q'):
        print("Shutting down collector.")
        break

cap.release()
cv2.destroyAllWindows()

