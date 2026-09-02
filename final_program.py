import serial
import time
import sys
import cv2
from ultralytics import YOLO

# Configuration
GRBL_PORT = '/dev/cu.usbserial-120' # Change This port to the one that shows up when you run "ls /dev/cu.*" in terminal
BAUD_RATE_GRBL = 115200

FEED_RATE_GANTRY = 5000  
FEED_RATE_CONVEYOR = 750

POS_START = (0, 0)
POS_WAIT = (100, 0)

POS_DROPOFF = {
    "glass-bottle": (2, 98),
    "plastic-bottle": (33, 98),
    "paper": (100, 98),
    "battery": (66, 98)
}

# Adjust these Svalues to change the angle of the servo
SERVO_PWM_HOME = 250   # Value to keep the basket down (bypass mode)
SERVO_PWM_EJECT = 425  # Value to raise the basket (eject mode)

# Initialisation

print("Loading YOLOv8 AI Model...")
model = YOLO('runs/detect/new_sorter-2/weights/best.pt')

print("Starting Webcam...")
cap = cv2.VideoCapture(0)
time.sleep(2) 

print("Connecting to hardware...")
try:
    arduino = serial.Serial(port=GRBL_PORT, baudrate=BAUD_RATE_GRBL, timeout=1)
    print(f"Gantry connected on {GRBL_PORT}")
except Exception as e:
    print(f"Gantry connection failed: {e}")
    sys.exit(1)

print("Establishing GBRL Connection...")
arduino.write(b'\r\n\r\n')
time.sleep(2)
arduino.reset_input_buffer()

print("Reformatting speed settings")
grbl_settings = [
    b'$32=0\n',     # IMPORTANT: Turn laser mode off so Spindle PWM works properly (for the ejection servo)
    b'$110=3000\n', # X-axis speed (mm/min / 4)
    b'$111=1000\n', # Conveyor speed (mm/min)
    b'$112=3000\n', # Z-axis speed (mm/min / 4)
    b'$120=150\n',  
    b'$121=500\n',  
    b'$122=150\n'   
]
for setting in grbl_settings:
    arduino.write(setting)
    time.sleep(0.1)
arduino.reset_input_buffer()

# Communication 

def send_gcode(cmd, wait_for_ok=True):
    # Safely sends gcode and prevents infinite hang loops.
    arduino.write(cmd.encode('utf-8'))
    if not wait_for_ok:
        return
    
    timeout = time.time() + 3.0 
    while time.time() < timeout:
        resp = arduino.readline().decode('utf-8').strip()
        if resp == 'ok':
            return
        if resp.lower().startswith('error'):
            print(f"  ↪ GRBL ERROR {resp} for command: {cmd.strip()}")
            return

def wait_for_idle():
    # Polls GRBL and prevents Python from hanging.
    time.sleep(0.1) 
    arduino.reset_input_buffer()
    timeout = time.time() + 10.0 
    
    while time.time() < timeout:
        arduino.write(b'?')
        resp = arduino.readline().decode('utf-8').strip()
        if resp.startswith('<Idle'):
            break
        elif resp.startswith('<Alarm'):
            print("GRBL alarm detected. Unlocking...")
            arduino.write(b'$X\n')
            time.sleep(0.5)
            break
        time.sleep(0.1)

print("Setting Home Position")
send_gcode('G92 X0 Y0 Z0\n')

def move_corexz(target_x, target_z):
    motor_a = target_z + target_x
    motor_b = target_z - target_x
    gcode = f"G90 G1 X{motor_a:.2f} Z{motor_b:.2f} F{FEED_RATE_GANTRY}\n"
    send_gcode(gcode)
    wait_for_idle()

def actuate_servo():
    # Uses GRBL Spindle PWM to move the servo
    print(f"Actuating servo (raising basket to S{350})...")
    send_gcode(f'M3 S{350}\n') 
    time.sleep(1.0) 
    
    print(f"Returning servo to bypass mode (S{0})...")
    send_gcode(f'M3 S{0}\n')
    time.sleep(0.5)
    print(f"Actuating servo (raising basket to S{SERVO_PWM_EJECT})...")
    send_gcode(f'M3 S{SERVO_PWM_EJECT}\n') 
    time.sleep(1.0) 
    
    print(f"Returning servo to bypass mode (S{SERVO_PWM_HOME})...")
    send_gcode(f'M3 S{0}\n')
    time.sleep(0.5)


def paper_servo():
    #ejects the paper at a steeper angle
    print(f"Actuating servo (raising basket to S{SERVO_PWM_EJECT})...")
    send_gcode(f'M3 S{SERVO_PWM_EJECT}\n') 
    time.sleep(1.0) 
    
    print(f"Returning servo to bypass mode (S{SERVO_PWM_HOME})...")
    send_gcode(f'M3 S{0}\n')
    time.sleep(0.5)

# YOLO functions

def check_for_object():
    ret, frame = cap.read()
    if not ret:
        return None
    
    results = model.predict(source=frame, show=False, conf=0.6, verbose=False)
    
    if results and len(results[0].boxes) > 0:
        class_id = int(results[0].boxes[0].cls[0])
        detected_name = model.names[class_id].lower()
            
        return detected_name
        
    return None 

# Sorting Loop

print("\n" + "="*40)
print("SORTING SEQUENCE INITIATED")
print("Press Ctrl+C to exit")
print("="*40)

# Initialize the servo to the flat/bypass position before starting
print("Homing Basket Servo...")
send_gcode(f'M3 S{0}\n')
time.sleep(1)

try:
    while True:
        print(f"\n[1] Parking gantry at scan position {POS_WAIT}...")
        move_corexz(POS_WAIT[0], POS_WAIT[1])

        print("[2] Spinning conveyor")
        
        # Flush the old webcam frames
        for _ in range(5):
            cap.grab()
            
        # Start the conveyor
        send_gcode(f'M3 S{SERVO_PWM_HOME}\n')
        send_gcode(f"$J=G91 Y-1000 F{FEED_RATE_CONVEYOR}\n")
        detected_item = None
        while not detected_item:
            detected_item = check_for_object()
            cv2.waitKey(1)
            # Re-trigger if the belt stops
            arduino.write(b'?')
            if arduino.readline().decode('utf-8').strip().startswith('<Idle'):
                 send_gcode(f"$J=G91 Y-1000 F{FEED_RATE_CONVEYOR}\n")
        
        print(f" - Detected: {detected_item.lower()}.")
        print("[3] Waiting for object to exit conveyor")
        time.sleep(0.2)
        arduino.write(b'\x85')
        wait_for_idle()
        while not detected_item:
            detected_item = check_for_object()
        print(f" - Checked: {detected_item.lower()}.")
        send_gcode(f'M3 S{0}\n')
        send_gcode(f"$J=G91 Y-1000 F{FEED_RATE_CONVEYOR}\n")
        while check_for_object() is not None:
            cv2.waitKey(1)
            
        print(" - Object cleared camera.")
        if detected_item in POS_DROPOFF:
            print(" - Known object confirmed. Indexing...")
            time.sleep(0.75)
            
            arduino.write(b'\x85')
            arduino.reset_input_buffer() 
            wait_for_idle()
            
            drop_x, drop_z = POS_DROPOFF[detected_item]
            print(f"[4] Moving gantry to {detected_item} position ({drop_x}, {drop_z})...")
            move_corexz(drop_x, drop_z)
            
            print("[5] Triggering ejection servo")
            if(detected_item != "paper"):
                actuate_servo()
            else:
                paper_servo()
            
        else:
            print(f"Unknown object '{detected_item}' detected. Ignoring and skipping wait.")
            # We MUST stop the conveyor here too, otherwise the loop restarts and crashes GRBL
            arduino.write(b'\x85')
            arduino.reset_input_buffer() 
            wait_for_idle()

except KeyboardInterrupt:
    print("\n\nSequence interrupted by user.")
    print("Releasing camera and stopping hardware...")
    cap.release()
    cv2.destroyAllWindows()
    
    # Send a quick stop and turn off the servo PWM signal
    arduino.write(b'\x85') 
    send_gcode('M5\n') # M5 turns off the spindle/servo signal safely
    time.sleep(0.1)
    # move the gantry back to the home position
    move_corexz(0, 0)
    wait_for_idle()
    time.sleep(0.5)
    
    arduino.close()
    print("Hardware safe to power down.")