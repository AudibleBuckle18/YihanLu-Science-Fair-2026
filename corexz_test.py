import serial
import time
import sys

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/cu.usbserial-120' 
BAUD_RATE = 115200

# Speed settings (Normalized back to 100% max)
MAX_SPEED_MM_MIN = 3000  
TARGET_PERCENT = 3.00    # 1.00 = 100% of max speed
FEED_RATE = int(MAX_SPEED_MM_MIN * TARGET_PERCENT) # Calculates to F3000

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
    b'$110=4000\n', # Max X Speed (mm/min)
    b'$111=4000\n', # Max Y Speed (mm/min)
    b'$112=4000\n', # Max Z Speed (mm/min)
    b'$120=1000\n',  # X Acceleration (mm/sec^2)
    b'$121=1000\n',  # Y Acceleration (mm/sec^2)
    b'$122=1000\n'   # Z Acceleration (mm/sec^2)
]
for setting in grbl_settings:
    arduino.write(setting)
    time.sleep(0.1)
arduino.flushInput()

# Set current physical location as HOME (0,0)
print("Setting current position as Bottom-Left Home (X=0, Z=0)...")
arduino.write(b'G92 X0 Y0\n')
response = arduino.readline().decode('utf-8').strip()
print(f"Arduino: {response}")

# ==========================================
# 🎮 MOVEMENT LOOP
# ==========================================
def move_corexz(target_x, target_z):
    # 1. Bounds Checking (0-95 for X, 0-100 for Z)
    if not (0 <= target_x <= 102):
        print(f"⚠️ Move canceled: X={target_x} is out of bounds (0 to 95 mm).")
        return
        
    if not (0 <= target_z <= 104):
        print(f"⚠️ Move canceled: Z={target_z} is out of bounds (0 to 100 mm).")
        return

    # 2. CoreXZ Kinematics Math (Swapped X and Z)
    # By swapping the inputs, we successfully flip the physical axes
    motor_a = target_z + target_x
    motor_b = target_z - target_x
    
    # Format the G-Code command
    gcode = f"G1 X{motor_a:.2f} Y{motor_b:.2f} F{FEED_RATE}\n"
    
    # Send to Arduino
    print(f"\nSending Command: {gcode.strip()}")
    arduino.write(gcode.encode('utf-8'))
    
    # Wait for the "ok" response from GRBL
    while True:
        resp = arduino.readline().decode('utf-8').strip()
        if resp == 'ok':
            print("✅ Move complete!")
            break
        elif resp != "":
            print(f"Arduino: {resp}")

# Interactive prompt
print("\n" + "="*40)
print("🚀 CORE-XZ CONTROL TERMINAL READY")
print(f"Current Speed: {TARGET_PERCENT*100}% ({FEED_RATE} mm/min)")
print("Limits: X(0 to 95), Z(0 to 100)")
print("Type 'q' to quit.")
print("="*40)

while True:
    try:
        user_input = input("\nEnter target coordinates (format: X Z) e.g., 50 25: ")
        
        if user_input.lower() == 'q':
            print("Closing connection...")
            arduino.close()
            break
            
        # Parse the input
        parts = user_input.split()
        if len(parts) != 2:
            print("⚠️ Invalid input. Please provide exactly two numbers separated by a space.")
            continue
            
        x_val = float(parts[0])
        z_val = float(parts[1])
        
        # Execute the move
        move_corexz(x_val, z_val)
        
    except ValueError:
        print("⚠️ Please enter valid numbers.")
    except KeyboardInterrupt:
        print("\nForce quitting...")
        arduino.close()
        break