import serial
import time
import sys

SERVO_PORT = '/dev/cu.usbserial-110' 
BAUD_RATE = 115200 
SERVO_ID = 1        # Universal Broadcast ID (Ignores programmed ID)

# Position Values (0 to 1000 range)
POS_HOME = 500  
POS_EJECT = 645 

print("\n" + "="*40)
print("🔧 HIWONDER SERVO DIAGNOSTIC TOOL")
print("="*40)

print(f"Connecting to BusLinker on {SERVO_PORT}...")
try:
    servo_board = serial.Serial(port=SERVO_PORT, baudrate=BAUD_RATE, timeout=1)
    print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Check your USB cable and port name!")
    sys.exit(1)

# ==========================================
# 🤖 MOVEMENT FUNCTION
# ==========================================
def move_hiwonder_servo(servo_id, position, time_ms):
    """Packages and sends the hex byte protocol to the Hiwonder BusLinker."""
    pos_l = position & 0xFF
    pos_h = (position >> 8) & 0xFF
    time_l = time_ms & 0xFF
    time_h = (time_ms >> 8) & 0xFF
    
    # Checksum calculation required by Hiwonder protocol
    checksum = (~(servo_id + 7 + 1 + pos_l + pos_h + time_l + time_h)) & 0xFF
    
    # Construct the byte array: Header, Header, ID, Length, CMD, Data..., Checksum
    packet = [0x55, 0x55, servo_id, 0x07, 0x01, pos_l, pos_h, time_l, time_h, checksum]
    
    # Send it down the USB cable
    servo_board.write(bytearray(packet))

time.sleep(1) # Brief pause after connecting

try:
    print("\nSending initial HOME command (Position 500)...")
    move_hiwonder_servo(SERVO_ID, POS_HOME, 1000)
    
    while True:
        input("\n🟢 Press ENTER to test Ejection Sequence (or Ctrl+C to quit)...")
        
        print("  ↪ Moving to 35º (Position 645)...")
        move_hiwonder_servo(SERVO_ID, POS_EJECT, 1000)
        time.sleep(1.5) # Wait for move + hold
        
        print("  ↪ Returning to 0º (Position 500)...")
        move_hiwonder_servo(SERVO_ID, POS_HOME, 500)

except KeyboardInterrupt:
    print("\n\n🛑 Closing diagnostic tool...")
    servo_board.close()
    print("Port closed safely.")