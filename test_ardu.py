import serial
import time

def send_command(ser, command):
    # Send the command with a newline
    ser.write((command + '\n').encode())
    # Allow some time for Arduino to process the command
    time.sleep(0.5)
    # Read and return all available data as a response
    response = ser.read_all().decode()
    return response

def main():
    # Replace 'COM3' with the appropriate serial port for your system
    ser_port = 'COM6'  # For Windows, e.g., 'COM3', or for Linux '/dev/ttyUSB0'
    baud_rate = 115200

    try:
        ser = serial.Serial(ser_port, baud_rate, timeout=1)
        print(f"Connected to {ser_port} at {baud_rate} baud.")
    except serial.SerialException as e:
        print("Error opening serial port:", e)
        return

    # Wait a couple of seconds for the Arduino to reset after serial connection
    time.sleep(2)

    # Optionally, read any initial messages from Arduino
    if ser.in_waiting > 0:
        initial = ser.read_all().decode()
        print("Initial data from Arduino:")
        print(initial)

    # Define a list of test commands (adjust as needed)
    test_commands = [
        "STATUS",
        "MOVE 120 0 345",
        "OPEN",
        "CLOSE",
        "HOME"
    ]

    # Send each command and print responses
    for cmd in test_commands:
        print(f"\nSending command: {cmd}")
        response = send_command(ser, cmd)
        print("Response:")
        print(response)
        # Pause a bit between commands
        time.sleep(1)

    ser.close()
    print("Serial connection closed.")

if __name__ == '__main__':
    main()