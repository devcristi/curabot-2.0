import serial.tools.list_ports
import time


def initialize_robot_arm():
    """
    Initialize robot arm with proper error handling and port detection
    """
    # List available ports
    available_ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"Available COM ports: {available_ports}")

    # Try to connect to COM6
    try:
        arm = serial.Serial('COM6', 115200, timeout=5)
        print("✅ Successfully connected to COM6")
        time.sleep(2)  # Wait for connection to stabilize
        return arm
    except serial.SerialException as e:
        if "PermissionError" in str(e):
            print("❌ Permission denied accessing COM6. Please check:")
            print("1. No other program is using the port")
            print("2. You have proper permissions/admin rights")
            print("3. The USB cable is properly connected")
        else:
            print(f"❌ Error connecting to COM6: {e}")
        return None


if __name__ == "__main__":
    print("Starting robot arm initialization...")
    arm = initialize_robot_arm()

    if arm is not None:
        print("Robot arm initialized successfully!")
        # Optional: close the port when done
        arm.close()
    else:
        print("Failed to initialize robot arm.")