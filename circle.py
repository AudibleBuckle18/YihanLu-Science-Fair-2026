import serial
import time
import sys
import math

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/cu.usbserial-11320' 
BAUD_RATE = 115200

# Speed settings
MAX_SPEED_MM_MIN = 8000  
TARGET_PERCENT = 1.00    
FEED_RATE = int(MAX_SPEED_MM_MIN * TARGET_PERCENT) 

# Circle Parameters
CENTER_X = 50
CENTER_Z = 50
RADIUS = 30
SEGMENTS = 60  # Number of straight-line segments to make up the circle

# ==========================================
# 🔌 CONNECTION & INITIALIZATION
# ==========================================
print(f"Connecting to Arduino on {SERIAL_PORT}...")
try:
    arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Wake up GRBL
print("Waking up GRBL...")
arduino.write(b'\r\n\r\n')
time.sleep(2)
arduino.flushInput()

# Override GRBL's internal EEPROM speed/acceleration caps
print("Unlocking GRBL's internal speed and acceleration limits...")
grbl_settings = [
    b'$110=8000\n', 
    b'$111=8000\n', 
    b'$112=8000\n', 
    b'$120=1000\n',  
    b'$121=1000\n',  
    b'$122=1000\n'   
]
for setting in grbl_settings:
    arduino.write(setting)
    time.sleep(0.1)
arduino.flushInput()

# Set current physical location as HOME (0,0)
print("Setting current position as Bottom-Left Home (X=0, Z=0)...")
# arduino.write(b'G92 X0 Z0\n')
response = arduino.readline().decode('utf-8').strip()
print(f"Arduino: {response}")

# ==========================================
# 📐 KINEMATICS & MOVEMENT FUNCTIONS
# ==========================================
def move_corexz(target_x, target_z):
    # CoreXZ Kinematics Math (Swapped X and Z as requested)
    motor_a = target_z + target_x
    motor_b = target_z - target_x
    
    # Format and send the G-Code command
    gcode = f"G1 X{motor_a:.3f} Z{motor_b:.3f} F{FEED_RATE}\n"
    arduino.write(gcode.encode('utf-8'))
    
    # Wait for the "ok" response from GRBL
    while True:
        resp = arduino.readline().decode('utf-8').strip()
        if resp == 'ok':
            break

# ==========================================
# 🔄 MAIN LOOP: DRAWING THE CIRCLE
# ==========================================
print("\n" + "="*40)
print("🚀 CONTINUOUS CIRCLE GENERATOR STARTED")
print(f"Center: ({CENTER_X}, {CENTER_Z}) | Radius: {RADIUS}")
print("Press Ctrl+C to stop the gantry and exit.")
print("="*40)

try:
    # 1. Move to the starting edge of the circle from (0,0) safely
    start_x = CENTER_X + RADIUS  # X = 80
    start_z = CENTER_Z           # Z = 50
    print(f"Moving to starting point ({start_x}, {start_z})...")
    move_corexz(start_x, start_z)

    loop_count = 1
    
    # 2. Continuously draw the circle
    while True:
        print(f"Drawing circle #{loop_count}...")
        
        for i in range(SEGMENTS + 1):
            # Calculate the angle in radians for this segment
            # 2 * pi is a full circle
            theta = (2 * math.pi / SEGMENTS) * i 
            
            # Calculate standard Cartesian coordinates
            point_x = CENTER_X + (RADIUS * math.cos(theta))
            point_z = CENTER_Z + (RADIUS * math.sin(theta))
            
            # Move the gantry to the calculated point
            move_corexz(point_x, point_z)
            
        loop_count += 1

except KeyboardInterrupt:
    print("\n\n🛑 Force quitting...")
    print("Stopping motors...")
    # Send a feed-hold command (!) to instantly stop GRBL, followed by closing the port
    arduino.write(b'!\n') 
    gcode = f"G1 X0 Z0 F{FEED_RATE}\n"
    arduino.write(gcode.encode('utf-8'))
    time.sleep(0.5)
    arduino.close()
    print("Connection closed. Safe to power down.")