import cv2

print("Knocking on camera ports 0 through 9...")

for i in range(10):
    # Try to open the camera port
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        # Read a single frame just to be absolutely sure it works
        ret, frame = cap.read()
        if ret:
            print(f"✅ SUCCESS: Camera found and streaming at index --> {i}")
        else:
            print(f"⚠️ FOUND, but couldn't read frame at index --> {i}")
        
        # Close the port so we don't lock it up
        cap.release()
    else:
        print(f"❌ Nothing at index {i}")

print("Search complete!")