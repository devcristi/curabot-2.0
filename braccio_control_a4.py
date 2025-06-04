import serial
import time
import math

# Valorile calibrate pentru poziția de 90 grade
ZERO_BASE = 90  # servo 1
ZERO_SHOUL = 85  # servo 2
ZERO_ELBOW = 85  # servo 3
ZERO_WRSTV = 103  # servo 4 (wrist flex)
ZERO_WRSTR = 20  # servo 5 (wrist rot)
ZERO_GRIP = 73  # servo 6 (gripper deschis)
ZERO_GRIP_CLOSED = 10  # gripper închis

# Configurare conexiune Arduino
ARDUINO_PORT = None  # Se va detecta automat
BAUDRATE = 9600

# Variabilă globală pentru conexiunea serială
arduino_connection = None

# DIMENSIUNI REALE BRACCIO (în mm)
# Acestea sunt dimensiunile aproximative ale brațului Braccio
BASE_HEIGHT = 72  # înălțimea bazei
SHOULDER_LENGTH = 125  # lungimea segmentului umăr
FOREARM_LENGTH = 125  # lungimea antebrațului
WRIST_LENGTH = 195  # lungimea încheieturii + gripper


def find_arduino_port():
    """Găsește portul Arduino automat"""
    import serial.tools.list_ports

    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB' in port.description:
            return port.device

    # Porturile comune Windows
    common_ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']
    for port in common_ports:
        try:
            ser = serial.Serial(port, BAUDRATE, timeout=1)
            ser.close()
            return port
        except:
            continue
    return None


def connect_to_arduino():
    """Conectează la Arduino și returnează obiectul serial"""
    global arduino_connection

    if arduino_connection and arduino_connection.is_open:
        return arduino_connection

    port = find_arduino_port()
    if not port:
        raise Exception("Nu s-a găsit portul Arduino! Verifică conexiunea USB.")

    try:
        arduino_connection = serial.Serial(port, BAUDRATE, timeout=5)
        time.sleep(3)  # Așteaptă inițializarea Arduino

        # Citește mesajele de inițializare
        while arduino_connection.in_waiting > 0:
            msg = arduino_connection.readline().decode('utf-8').strip()
            print(f"Arduino: {msg}")

        print(f"✅ Conectat la Arduino pe {port}")
        return arduino_connection

    except Exception as e:
        raise Exception(f"Eroare conectare Arduino: {e}")


def send_arduino_command(command):
    """Trimite comandă la Arduino și așteaptă răspuns"""
    ser = connect_to_arduino()

    ser.write((command + '\n').encode())
    time.sleep(0.1)

    # Așteaptă răspuns
    timeout = 10  # secunde
    start_time = time.time()

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            return response
        time.sleep(0.1)

    return "TIMEOUT"


def move_robot_servos(base, shoulder, elbow, wrist_ver, wrist_rot, gripper, step_delay=20):
    """Mișcă robotul la pozițiile specificate pentru servo-uri"""
    # Verifică limitele
    positions = [base, shoulder, elbow, wrist_ver, wrist_rot, gripper]
    for i, pos in enumerate(positions):
        if not (0 <= pos <= 180):
            raise ValueError(f"Poziția servo {i + 1} ({pos}) este în afara limitelor (0-180)")

    # Construiește comanda
    command = f"MOVE:{step_delay},{base},{shoulder},{elbow},{wrist_ver},{wrist_rot},{gripper}"

    response = send_arduino_command(command)

    if response == "MOVE_COMPLETE":
        print(
            f"✅ Robot mutat la pozițiile: B={base}, S={shoulder}, E={elbow}, WV={wrist_ver}, WR={wrist_rot}, G={gripper}")
        return True
    else:
        print(f"❌ Eroare mișcare robot: {response}")
        return False


def calculate_inverse_kinematics_corrected(x, y, z):
    """
    Calculează cinematica inversă CORECTATĂ pentru brațul Braccio.

    Parametri:
    x, y, z: coordonatele țintă în mm (relative la baza robotului)

    Returnează:
    tuple cu unghiurile pentru (base, shoulder, elbow, wrist_ver)
    """

    print(f"🔧 Calculez cinematica inversă pentru: x={x}, y={y}, z={z}")

    # Calculează unghiul bazei
    base_angle = math.degrees(math.atan2(y, x))
    # Ajustează pentru sistemul Braccio (0-180 grade)
    base_angle = base_angle + 90  # Transformă din (-90,90) în (0,180)
    base_angle = max(0, min(180, base_angle))

    # Calculează distanța orizontală de la baza robotului
    horizontal_distance = math.sqrt(x * x + y * y)

    # Ajustează înălțimea pentru înălțimea bazei
    adjusted_z = z - BASE_HEIGHT

    # Calculează distanța de la articulația umărului la țintă
    target_distance = math.sqrt(horizontal_distance * horizontal_distance + adjusted_z * adjusted_z)

    print(f"📏 Distanța orizontală: {horizontal_distance:.1f}mm")
    print(f"📏 Distanța țintă: {target_distance:.1f}mm")

    # Verifică dacă ținta este accesibilă
    max_reach = SHOULDER_LENGTH + FOREARM_LENGTH + WRIST_LENGTH
    if target_distance > max_reach:
        print(f"⚠️ Ținta prea departe! Distanța: {target_distance:.1f}mm, Maxim: {max_reach}mm")
        # Scalează coordonatele pentru a ajunge la limita
        scale = max_reach * 0.9 / target_distance
        horizontal_distance *= scale
        adjusted_z *= scale
        target_distance = math.sqrt(horizontal_distance * horizontal_distance + adjusted_z * adjusted_z)

    try:
        # Calculează unghiul cotului folosind legea cosinusurilor
        # Pentru Braccio, considerăm umărul și antebrațul ca segmente principale
        L1 = SHOULDER_LENGTH
        L2 = FOREARM_LENGTH + WRIST_LENGTH  # Antebrațul + încheietura

        cos_elbow = (L1 * L1 + L2 * L2 - target_distance * target_distance) / (2 * L1 * L2)
        cos_elbow = max(-1, min(1, cos_elbow))  # Limitează pentru acos
        elbow_angle = math.degrees(math.acos(cos_elbow))

        # Calculează unghiul umărului
        alpha = math.atan2(adjusted_z, horizontal_distance)
        beta = math.acos((L1 * L1 + target_distance * target_distance - L2 * L2) / (2 * L1 * target_distance))
        shoulder_angle = math.degrees(alpha + beta)

        # Ajustează pentru sistemul de coordonate Braccio
        # În Braccio, 90° înseamnă orizontal
        shoulder_angle = 90 - shoulder_angle
        elbow_angle = 180 - elbow_angle

        # Limitează unghiurile în intervalul valid Braccio
        base_angle = max(0, min(180, base_angle))
        shoulder_angle = max(15, min(165, shoulder_angle))  # Limitări fizice Braccio
        elbow_angle = max(0, min(180, elbow_angle))

        # Wrist vertical pentru a menține orientarea perpendiculară
        wrist_ver_angle = ZERO_WRSTV

        print(f"📐 Unghiuri calculate: Base={base_angle:.1f}°, Shoulder={shoulder_angle:.1f}°, Elbow={elbow_angle:.1f}°")

        return base_angle, shoulder_angle, elbow_angle, wrist_ver_angle

    except Exception as e:
        print(f"❌ Eroare calcul cinematică inversă: {e}")
        # Returnează pozițiile calibrate ca fallback
        return ZERO_BASE, ZERO_SHOUL, ZERO_ELBOW, ZERO_WRSTV


def a4_to_robot_coords_corrected(a4_x, a4_y, z):
    """
    Transformă coordonatele din sistemul A4 în coordonate robot CORECTATE.

    Sistemul A4: 4 foi A4 în peisaj (594mm x 420mm total)
    - Originea (0,0) la colțul stânga-sus
    - Centrul tău real: x=200mm, y=300mm în sistemul A4

    Pentru a transforma în coordonatele robotului, presupunem că:
    - Robotul este poziționat astfel încât să poată atinge întreaga suprafață A4
    - Centrul spațiului de lucru al robotului corespunde centrului fizic măsurat
    """

    # Centrul sistemului A4 (centrul fizic măsurat de tine)
    a4_center_x = 200  # mm
    a4_center_y = 300  # mm

    # Presupunem că robotul poate atinge o zonă de aproximativ 400mm x 400mm
    # și că centrul acestei zone corespunde centrului A4 măsurat
    robot_workspace_center_x = 250  # Distanța de la baza robotului la centrul zonei de lucru
    robot_workspace_center_y = 0  # Robotul este centrat pe axa Y

    # Calculează offsetul față de centrul A4
    offset_x = a4_x - a4_center_x
    offset_y = a4_y - a4_center_y

    # Transformă în coordonatele robotului
    robot_x = robot_workspace_center_x + offset_x
    robot_y = robot_workspace_center_y + offset_y
    robot_z = z

    print(f"🔄 Transformare A4->Robot: ({a4_x},{a4_y}) -> ({robot_x:.1f},{robot_y:.1f},{robot_z})")

    return robot_x, robot_y, robot_z


def go_to_coordinate(x, y, z, grip_position="closed"):
    """
    Mută robotul la coordonatele specificate în spațiul de lucru.

    Parametri:
    x, y, z: coordonatele țintă în mm
    grip_position: "closed", "open" sau valoare numerică (0-180)
    """

    print(f"🎯 Mergând la coordonatele: ({x}, {y}, {z})")

    # Calculează cinematica inversă
    base, shoulder, elbow, wrist_ver = calculate_inverse_kinematics_corrected(x, y, z)

    # Setează poziția gripperului
    if grip_position == "closed":
        gripper = ZERO_GRIP_CLOSED
    elif grip_position == "open":
        gripper = ZERO_GRIP
    else:
        gripper = int(grip_position)

    # Wrist rotation rămâne constant
    wrist_rot = ZERO_WRSTR

    # Mișcă robotul
    success = move_robot_servos(
        int(base), int(shoulder), int(elbow),
        int(wrist_ver), int(wrist_rot), int(gripper)
    )

    return success


def move_to_a4_position(a4_x, a4_y, z=150, grip="open"):
    """
    Primește coordonate în sistemul A4 și mută brațul robotic la poziția calculată.

    Parametri:
    a4_x: coordonata pe axa orizontală din sistemul A4 (mm)
    a4_y: coordonata pe axa verticală din sistemul A4 (mm)
    z: înălțimea dorită (mm); implicit 150 mm (mai aproape de suprafață)
    grip: starea gripperului, "closed", "open" sau valoare numerică
    """

    # Transformă coordonatele A4 în coordonate robot
    robot_coords = a4_to_robot_coords_corrected(a4_x, a4_y, z)

    print(f"📍 A4 ({a4_x}, {a4_y}) -> Robot {robot_coords}")

    # Mută robotul la poziția calculată
    return go_to_coordinate(*robot_coords, grip_position=grip)


def calibrate_center_position():
    """
    Funcție de calibrare pentru a testa centrul spațiului de lucru
    """
    print("🎯 CALIBRARE CENTRU SPAȚIU DE LUCRU")
    print("Această funcție va muta robotul la centrul calculat al spațiului A4")

    try:
        connect_to_arduino()

        # Poziția HOME mai întâi
        print("🏠 Mergând la HOME...")
        go_home()
        time.sleep(2)

        # Testează centrul real măsurat (200mm, 300mm în sistemul A4)
        center_a4_x = 200
        center_a4_y = 300
        center_z = 100  # Înălțime sigură pentru test

        print(f"📍 Testez centrul la A4({center_a4_x}, {center_a4_y}, {center_z})")

        success = move_to_a4_position(center_a4_x, center_a4_y, center_z, grip="open")

        if success:
            print("✅ Robot la centrul calculat!")
            print("🔍 Verifică dacă robotul este deasupra centrului fizic al spațiului A4")
            print("🔧 Dacă nu, ajustează valorile în funcția a4_to_robot_coords_corrected()")
        else:
            print("❌ Eroare la mutarea robotului")

    except Exception as e:
        print(f"❌ Eroare calibrare: {e}")
    finally:
        input("⏳ Apasă ENTER pentru a reveni la HOME...")
        go_home()
        close_connection()


def go_home():
    """Mută robotul la poziția HOME calibrată"""
    print("🏠 Mergând la poziția HOME...")
    response = send_arduino_command("HOME")
    if response == "HOME_COMPLETE":
        print("✅ Robot la poziția HOME")
        return True
    else:
        print(f"❌ Eroare HOME: {response}")
        return False


def close_connection():
    """Închide conexiunea cu Arduino"""
    global arduino_connection
    if arduino_connection and arduino_connection.is_open:
        arduino_connection.close()
        print("🔌 Conexiune Arduino închisă")


def test_coordinates_corrected():
    """
    Testează transformarea corectată a coordonatelor
    """
    print("=== TEST COORDONATE A4 CORECTAT ===")

    # Puncte de test
    test_points = [
        ("Centru Real Măsurat", (200, 300)),
        ("Colț Stânga Sus", (50, 50)),
        ("Colț Dreapta Sus", (350, 50)),
        ("Colț Stânga Jos", (50, 350)),
        ("Colț Dreapta Jos", (350, 350))
    ]

    z = 120  # Înălțime de test

    print(f"Înălțime de test: {z}mm\n")

    # Afișează coordonatele calculate
    for name, (a4_x, a4_y) in test_points:
        robot_coords = a4_to_robot_coords_corrected(a4_x, a4_y, z)
        print(
            f"{name:20}: A4({a4_x:3.0f}, {a4_y:3.0f}) -> Robot({robot_coords[0]:.1f}, {robot_coords[1]:.1f}, {robot_coords[2]:.1f})")

    # Test cu robotul
    print("\n" + "=" * 50)
    test_with_robot = input("🤖 Testezi cu robotul? (y/n): ").lower() == 'y'

    if test_with_robot:
        print("\n🚨 ATENȚIE: Robotul se va mișca! Verifică că zona este liberă.")
        input("Apasă ENTER pentru a continua...")

        try:
            connect_to_arduino()
            go_home()
            time.sleep(2)

            # Testează doar centrul pentru început
            name, (a4_x, a4_y) = test_points[0]  # Centru Real

            input(f"\n⏳ Apasă ENTER pentru {name}...")

            success = move_to_a4_position(a4_x, a4_y, z, grip="open")
            if success:
                print(f"✅ Robot la {name}")
                print("🔍 Verifică dacă robotul este la poziția corectă!")
                time.sleep(5)
            else:
                print(f"❌ Eroare la {name}")

            go_home()

        except Exception as e:
            print(f"❌ Eroare test: {e}")
        finally:
            close_connection()


if __name__ == "__main__":
    print("🤖 BRACCIO CONTROL - VERSIUNE CORECTATĂ")
    print("1. Calibrare centru - calibrate_center_position()")
    print("2. Test coordonate - test_coordinates_corrected()")
    print()

    choice = input("Alege opțiunea (1/2): ")

    if choice == "1":
        calibrate_center_position()
    elif choice == "2":
        test_coordinates_corrected()
    else:
        print("Opțiune invalidă!")