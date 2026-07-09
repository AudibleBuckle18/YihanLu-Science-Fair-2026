import cv2
import os
import time # Add this to use timestamps!

# CHANGE THIS TEXT FOR EACH NEW PART YOU PHOTOGRAPH
part_name = "spring" 

save_dir = "vex_dataset"
os.makedirs(save_dir, exist_ok=True)
# ... rest of the script remains the same ...

# Connect to your locked-in USB camera
cap = cv2.VideoCapture(0) # Use the index you confirmed earlier
img_count = 0

print("🚀 VEX Data Collector Armed!")
print("👉 Press 's' to SNAP a photo.")
print("👉 Press 'q' to QUIT.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("❌ Failed to grab frame.")
        break

    # Show the live feed
    cv2.imshow("VEX Data Collector", frame)

    # Wait for a key press
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        # Save the frame as a PNG# Old: img_name = os.path.join(save_dir, f"vex_frame_{img_count}.png")
        img_name = os.path.join(save_dir, f"{part_name}_{int(time.time())}.png")
        cv2.imwrite(img_name, frame)
        print(f"✅ Saved: {img_name}")
        img_count += 1

    elif key == ord('q'):
        print("🛑 Shutting down collector.")
        break

cap.release()
cv2.destroyAllWindows()
