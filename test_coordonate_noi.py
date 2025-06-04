import serial
import time

# Valorile calibrate pentru poziția de 90 grade
ZERO_BASE = 90  # servo 1
ZERO_SHOUL = 85  # servo 2
ZERO_ELBOW = 85  # servo 3
ZERO_WRSTV = 103  # servo 4 (wrist flex)
ZERO_WRSTR = 20  # servo 5 (wrist rot)
ZERO_GRIP = 73  # servo 6 (gripper deschis)


class CalibratedBraccio:
    def __init__(self, port='COM6', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect()

    def find_arduino_port(self):
        """Găsește portul Arduino automat"""
        import serial.tools.list_ports

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Arduino' in port.description or 'CH340' in port.description or 'USB' in port.description:
                return port.device

        # Porturile comune
        common_ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8']
        for port in common_ports:
            try:
                ser = serial.Serial(port, 9600, timeout=1)
                ser.close()
                return port
            except:
                continue
        return None

    def connect(self):
        """Conectează la Arduino"""
        if not self.port:
            self.port = self.find_arduino_port()

        if not self.port:
            raise Exception("Nu s-a găsit portul Arduino!")

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=5)
            time.sleep(3)  # Așteaptă inițializarea Arduino

            # Citește mesajul de inițializare
            while self.ser.in_waiting > 0:
                msg = self.ser.readline().decode('utf-8').strip()
                print(f"Arduino: {msg}")

            print(f"✅ Conectat la {self.port}")

        except Exception as e:
            raise Exception(f"Eroare conectare: {e}")

    def send_command(self, command):
        """Trimite comandă la Arduino și așteaptă răspuns"""
        if not self.ser:
            raise Exception("Nu există conexiune cu Arduino!")

        self.ser.write((command + '\n').encode())
        time.sleep(0.1)

        # Așteaptă răspuns
        timeout = 10  # secunde
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8').strip()
                return response
            time.sleep(0.1)

        return "TIMEOUT"

    def move_to_position(self, base, shoulder, elbow, wrist_ver, wrist_rot, gripper, step_delay=20):
        """Mișcă robotul la poziția specificată"""
        # Verifică limitele (0-180 pentru majoritatea servo-urilor)
        positions = [base, shoulder, elbow, wrist_ver, wrist_rot, gripper]
        for i, pos in enumerate(positions):
            if not (0 <= pos <= 180):
                raise ValueError(f"Poziția servo {i + 1} ({pos}) este în afara limitelor (0-180)")

        # Construiește comanda
        command = f"MOVE:{step_delay},{base},{shoulder},{elbow},{wrist_ver},{wrist_rot},{gripper}"

        print(f"Trimit: {command}")
        response = self.send_command(command)

        if response == "MOVE_COMPLETE":
            print("✅ Mișcare completă")
            return True
        else:
            print(f"❌ Eroare mișcare: {response}")
            return False

    def go_home(self):
        """Merge la poziția HOME (calibrată)"""
        print("Mergând la poziția HOME calibrată...")
        response = self.send_command("HOME")
        return response == "HOME_COMPLETE"

    def go_to_90_degrees(self):
        """Merge la poziția calibrată de 90 grade"""
        print("Mergând la poziția calibrată de 90 grade...")
        response = self.send_command("CALIBRATED_90")
        return response == "CALIBRATED_90_COMPLETE"

    def test_movement(self):
        """Testează mișcările de bază"""
        print("\n=== TEST MIȘCĂRI CALIBRATE ===")

        # 1. Poziția calibrată de 90 grade
        print("\n1. Poziția calibrată de 90 grade:")
        if self.go_to_90_degrees():
            print("✅ Poziția de 90 grade OK")
            time.sleep(2)

        # 2. Test mișcare manuală cu valorile calibrate
        print("\n2. Test cu valorile calibrate:")
        success = self.move_to_position(
            ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW,
            ZERO_WRSTV, ZERO_WRSTR, ZERO_GRIP
        )

        if success:
            print("✅ Mișcare cu valori calibrate OK")
            time.sleep(2)

        # 3. Test gripper
        print("\n3. Test gripper:")
        # Închide gripper
        self.move_to_position(ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW, ZERO_WRSTV, ZERO_WRSTR, 10)
        time.sleep(1)
        # Deschide gripper
        self.move_to_position(ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW, ZERO_WRSTV, ZERO_WRSTR, ZERO_GRIP)

        print("✅ Test gripper OK")

    def close(self):
        """Închide conexiunea"""
        if self.ser:
            self.ser.close()
            print("Conexiune închisă")


def test_calibrated_robot():
    """Test pentru robotul calibrat"""
    try:
        # Conectează la robot
        robot = CalibratedBraccio()

        # Testează mișcările
        robot.test_movement()

        # Întrebare utilizator
        while True:
            print("\n" + "=" * 40)
            print("Opțiuni:")
            print("1. Poziția de 90 grade calibrată")
            print("2. HOME")
            print("3. Test gripper")
            print("4. Mișcare personalizată")
            print("5. Ieșire")

            choice = input("Alege opțiunea (1-5): ")

            if choice == "1":
                robot.go_to_90_degrees()
            elif choice == "2":
                robot.go_home()
            elif choice == "3":
                print("Închid gripper...")
                robot.move_to_position(ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW, ZERO_WRSTV, ZERO_WRSTR, 10)
                time.sleep(1)
                print("Deschid gripper...")
                robot.move_to_position(ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW, ZERO_WRSTV, ZERO_WRSTR, ZERO_GRIP)
            elif choice == "4":
                try:
                    base = int(input(f"Base ({ZERO_BASE}): ") or ZERO_BASE)
                    shoulder = int(input(f"Shoulder ({ZERO_SHOUL}): ") or ZERO_SHOUL)
                    elbow = int(input(f"Elbow ({ZERO_ELBOW}): ") or ZERO_ELBOW)
                    wrist_v = int(input(f"Wrist Ver ({ZERO_WRSTV}): ") or ZERO_WRSTV)
                    wrist_r = int(input(f"Wrist Rot ({ZERO_WRSTR}): ") or ZERO_WRSTR)
                    gripper = int(input(f"Gripper ({ZERO_GRIP}): ") or ZERO_GRIP)

                    robot.move_to_position(base, shoulder, elbow, wrist_v, wrist_r, gripper)
                except ValueError:
                    print("Valori invalide!")
            elif choice == "5":
                break
            else:
                print("Opțiune invalidă!")

        robot.close()

    except Exception as e:
        print(f"Eroare: {e}")


if __name__ == "__main__":
    test_calibrated_robot()