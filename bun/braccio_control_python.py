import serial
import time
import solverNNA
import numpy as np

base = [90, 0, 180, 0]  # [default, min, max, index]
shoulder = [150, 15, 165, 1]
elbow = [0, 0, 180, 2]
wrist = [0, 0, 180, 3]
wristRot = [0, 0, 180, 4]
gripper = [73, 73, 0, 5]

arm = serial.Serial('COM6', 115200, timeout=5)
print("Initializing arm")
time.sleep(2)
arm.write(b'H0,90,20,90,90,73,20\n')  # home at low speeds
time.sleep(2)


def write_arduino(angles):
    # angles: [base, shoulder, elbow, wrist, wristRot, gripper]
    angles[0] = 180 - angles[0]  # invert base
    angles[3] = 180 - angles[3]  # invert wrist vertical
    angle_string = ','.join(str(elem) for elem in angles)
    angle_string = "P" + angle_string + ",200\n"
    arm.write(angle_string.encode())


def rotate_joint(joint):
    # joint = [default, min, max, index]
    def calculate_joint(joint, number):
        defaults = [
            base[0],
            shoulder[0],
            elbow[0],
            wrist[0],
            wristRot[0],
            gripper[0]
        ]
        defaults[joint[3]] = joint[number]
        write_arduino(defaults)

    calculate_joint(joint, 1)
    time.sleep(2)
    calculate_joint(joint, 2)
    time.sleep(2)
    calculate_joint(joint, 1)
    time.sleep(2)


def home(speed=20):
    defaults = [base[0], shoulder[0], elbow[0], wrist[0], wristRot[0], gripper[0]]
    write_arduino(defaults)


def rotate_all_joints():
    print("The base.")
    rotate_joint(base)
    print("The shoulder.")
    rotate_joint(shoulder)
    print("The elbow.")
    rotate_joint(elbow)
    print("The vertical axis of the wrist.")
    rotate_joint(wrist)
    print("The rotational axis of the wrist.")
    rotate_joint(wristRot)
    print("The gripper.")
    rotate_joint(gripper)


def write_position(
        theta_base=base[0],
        theta_shoulder=shoulder[0],
        theta_elbow=elbow[0],
        theta_wrist=wrist[0],
        theta_wristRot=wristRot[0],
        grip="closed"
):
    if grip == "closed":
        theta_gripper = gripper[1]
    else:  # "open"
        theta_gripper = gripper[2]

    theta_base_comp = solverNNA.backlash_compensation_base(theta_base)
    angles_to_send = [
        theta_base_comp,
        theta_shoulder,
        theta_elbow,
        theta_wrist,
        theta_wristRot,
        theta_gripper
    ]
    write_arduino(angles_to_send)

    # Salvăm valori întregi (sigure) în prev_teta.txt
    int_angles = [
        int(theta_base),
        int(theta_shoulder),
        int(theta_elbow),
        int(theta_wrist),
        int(theta_wristRot),
        int(theta_gripper)
    ]
    with open("prev_teta.txt", "w") as f:
        for a in int_angles:
            f.write(f"{a};")


def get_previous_teta():
    with open("prev_teta.txt", "r") as f:
        prev_string = f.read()
    parts = prev_string.split(";")
    if parts and parts[-1] == "":
        parts.pop()
    return [int(float(x)) for x in parts]  # convertim sigur float→int


def go_to_coordinate(x, y, z, grip_position="closed"):
    theta_list = solverNNA.move_to_position_cart(x, y, z)
    theta0 = theta_list[0] + 90
    if theta0 > 180:
        theta0 -= 180
    write_position(
        theta_base=theta0,
        theta_shoulder=theta_list[1],
        theta_elbow=theta_list[2],
        theta_wrist=theta_list[3],
        theta_wristRot=wristRot[0],  # rămâne default
        grip=grip_position
    )


def move_vertical(x, y):
    for z in np.linspace(0, 350, 2):
        print(f"Z = {z}")
        go_to_coordinate(x, y, int(z))
        time.sleep(2)


def move_horizontal(z):
    for x in np.linspace(100, 350, 2):
        print(f"X = {x}")
        go_to_coordinate(int(x), 0, z)
        time.sleep(2)


def open_gripper():
    prev = get_previous_teta()
    write_position(
        prev[0], prev[1], prev[2], prev[3],
        prev[4],  # wristRot rămâne ce a fost
        grip="open"
    )


def close_gripper():
    prev = get_previous_teta()
    write_position(
        prev[0], prev[1], prev[2], prev[3],
        prev[4],  # wristRot rămâne ce a fost
        grip="closed"
    )


def backlash():
    time.sleep(5)
    write_position(90, 0, 90, 90)
    time.sleep(2)
    write_position(45, 0, 90, 90)
    time.sleep(2)
    write_position(90, 0, 90, 90)


def camera_compensation(x_coordinate, y_coordinate):
    h_foam = 80
    cam = [480, 150, 880]
    offset = 300
    xc = (offset - x_coordinate) + (cam[0] - offset)
    x_comp = xc - (h_foam / (cam[2] / xc))
    if y_coordinate < cam[1]:
        y_comp = y_coordinate - (h_foam / (cam[2] / y_coordinate))
    else:
        y_comp = y_coordinate + (h_foam / (cam[2] / y_coordinate))
    x_comp = offset - (x_comp - (cam[0] - offset))
    return int(x_comp), int(y_comp)


def pick(x, y):
    """
    Funcție îmbunătățită pentru a prelua un obiect la coordonatele (x, y).
    Se aplecă mai mult pentru obiectele mai îndepărtate de (200, 0).
    """
    # Coordonatele fixe pentru depunere
    DROP_X = 200
    DROP_Y = 100
    DROP_Z = 50  # Înălțime sigură pentru depunere

    # Calculăm distanța față de punctul de referință (200, 0)
    distance = ((x - 200) ** 2 + (y - 0) ** 2) ** 0.5

    # Ajustăm z-ul de preluare în funcție de distanță
    if distance > 150:
        pick_z = -80  # Se aplecă mai mult pentru obiectele îndepărtate
        print(f"→ Obiect îndepărtat (distanța: {distance:.1f}mm) - coborâre adâncă")
    elif distance > 100:
        pick_z = -65  # Coborâre medie
        print(f"→ Obiect la distanță medie (distanța: {distance:.1f}mm) - coborâre medie")
    else:
        pick_z = -50  # Coborâre standard
        print(f"→ Obiect aproape (distanța: {distance:.1f}mm) - coborâre standard")

    print(f"→ Încep preluarea obiectului de la ({x}, {y}) cu z={pick_z}mm ...")

    # Pas 1: Mergem la poziția de deasupra obiectului (z = 50mm) cu gripper deschis
    print("→ Merg deasupra obiectului ...")
    go_to_coordinate(x, y, 50, grip_position="open")
    time.sleep(1)

    # Pas 2: Coborâm treptat pentru preluare (z ajustat pe distanță)
    print(f"→ Cobor pentru preluare la z={pick_z}mm ...")
    go_to_coordinate(x, y, pick_z, grip_position="open")
    time.sleep(1.5)

    # Pas 3: Închidem gripper-ul pentru a prinde obiectul
    print("→ Prind obiectul ...")
    close_gripper()
    time.sleep(1)

    # Pas 4: Ridicăm obiectul la o înălțime sigură (z = 50mm)
    print("→ Ridic obiectul la înălțime sigură ...")
    go_to_coordinate(x, y, 50, grip_position="closed")
    time.sleep(1)

    # Pas 5: Mergem la poziția de depunere (x=200, y=100, z=50)
    print(f"→ Merg la zona de depunere ({DROP_X}, {DROP_Y}, {DROP_Z}) ...")
    go_to_coordinate(DROP_X, DROP_Y, DROP_Z, grip_position="closed")
    time.sleep(1.5)

    # Pas 6: Coborâm pentru depunere (z = -30mm pentru a fi mai aproape de suprafață)
    print("→ Cobor pentru depunere ...")
    go_to_coordinate(DROP_X, DROP_Y, -30, grip_position="closed")
    time.sleep(1)

    # Pas 7: Deschidem gripper-ul pentru a elibera obiectul
    print("→ Eliberez obiectul ...")
    open_gripper()
    time.sleep(1)

    # Pas 8: Ridicăm brațul la înălțime sigură după depunere
    print("→ Retrag brațul la înălțime sigură ...")
    go_to_coordinate(DROP_X, DROP_Y, 50, grip_position="open")
    time.sleep(1)

    print("✅ Preluare și depunere completată cu succes!")

    # Pas 9: Mergem la poziția HOME
    print("→ Merg la poziția HOME ...")
    home()
    time.sleep(2)
    print("✅ Poziție HOME atinsă!")


def pick_smooth_v2(x, y):
    """
    Versiune alternativă cu mișcare încă mai fluidă și ajustare pe distanță
    """
    DROP_X = 200
    DROP_Y = 100

    # Calculăm distanța față de punctul de referință (200, 0)
    distance = ((x - 200) ** 2 + (y - 0) ** 2) ** 0.5

    # Ajustăm z-ul de preluare în funcție de distanță
    if distance > 150:
        pick_z = -80
        print(f"→ Obiect îndepărtat (distanța: {distance:.1f}mm) - coborâre adâncă")
    elif distance > 100:
        pick_z = -65
        print(f"→ Obiect la distanță medie (distanța: {distance:.1f}mm) - coborâre medie")
    else:
        pick_z = -50
        print(f"→ Obiect aproape (distanța: {distance:.1f}mm) - coborâre standard")

    print(f"→ Încep preluarea fluidă a obiectului de la ({x}, {y}) ...")

    # Pas 1: Poziție intermediară de siguranță
    print("→ Merg la poziție intermediară ...")
    go_to_coordinate(x, y, 100, grip_position="open")
    time.sleep(0.8)

    # Pas 2: Apropiere de obiect
    print("→ Mă apropii de obiect ...")
    go_to_coordinate(x, y, 20, grip_position="open")
    time.sleep(0.8)

    # Pas 3: Preluare finală cu z ajustat
    print(f"→ Preluare finală la z={pick_z}mm ...")
    go_to_coordinate(x, y, pick_z, grip_position="open")
    time.sleep(1)

    # Pas 4: Prindere
    print("→ Prind obiectul ...")
    close_gripper()
    time.sleep(0.8)

    # Pas 5: Ridicare treptată
    print("→ Ridic treptat ...")
    go_to_coordinate(x, y, 20, grip_position="closed")
    time.sleep(0.8)
    go_to_coordinate(x, y, 80, grip_position="closed")
    time.sleep(0.8)

    # Pas 6: Mișcare către zona de depunere - poziție intermediară
    mid_x = (x + DROP_X) // 2
    mid_y = (y + DROP_Y) // 2
    print(f"→ Mișcare intermediară către ({mid_x}, {mid_y}) ...")
    go_to_coordinate(mid_x, mid_y, 100, grip_position="closed")
    time.sleep(1)

    # Pas 7: Apropiere de zona de depunere
    print(f"→ Ajung la zona de depunere ...")
    go_to_coordinate(DROP_X, DROP_Y, 80, grip_position="closed")
    time.sleep(0.8)

    # Pas 8: Depunere
    print("→ Cobor pentru depunere ...")
    go_to_coordinate(DROP_X, DROP_Y, -20, grip_position="closed")
    time.sleep(1)

    # Pas 9: Eliberare
    print("→ Eliberez obiectul ...")
    open_gripper()
    time.sleep(0.8)

    # Pas 10: Retragere finală
    print("→ Retrag brațul ...")
    go_to_coordinate(DROP_X, DROP_Y, 80, grip_position="open")
    time.sleep(0.8)

    print("✅ Preluare și depunere fluidă completată!")

    # Pas 11: Mergem la poziția HOME
    print("→ Merg la poziția HOME ...")
    home()
    time.sleep(2)
    print("✅ Poziție HOME atinsă!")


def pick_adaptive(x, y):
    """
    Versiune cu ajustare foarte precisă pe distanță și unghi
    """
    DROP_X = 200
    DROP_Y = 100

    # Calculăm distanța față de punctul de referință (200, 0)
    distance = ((x - 200) ** 2 + (y - 0) ** 2) ** 0.5

    # Calculăm unghiul pentru a vedea în ce direcție este obiectul
    angle = np.arctan2(y - 0, x - 200) * 180 / np.pi

    # Ajustăm z-ul de preluare foarte precis
    if distance > 200:
        pick_z = -90  # Foarte adânc pentru obiectele foarte îndepărtate
    elif distance > 150:
        pick_z = -80  # Adânc pentru obiectele îndepărtate
    elif distance > 100:
        pick_z = -65  # Mediu
    elif distance > 50:
        pick_z = -55  # Puțin mai adânc decât standard
    else:
        pick_z = -50  # Standard

    print(f"→ Obiect la distanța {distance:.1f}mm, unghiul {angle:.1f}° - coborâre la z={pick_z}mm")

    print(f"→ Încep preluarea adaptivă a obiectului de la ({x}, {y}) ...")

    go_to_coordinate(x, y, 50, grip_position="open")
    time.sleep(1)

    go_to_coordinate(x, y, pick_z, grip_position="open")
    time.sleep(1.5)

    close_gripper()
    time.sleep(1)

    go_to_coordinate(x, y, 50, grip_position="closed")
    time.sleep(1)

    go_to_coordinate(DROP_X, DROP_Y, 50, grip_position="closed")
    time.sleep(1.5)

    go_to_coordinate(DROP_X, DROP_Y, -30, grip_position="closed")
    time.sleep(1)

    open_gripper()
    time.sleep(1)

    go_to_coordinate(DROP_X, DROP_Y, 50, grip_position="open")
    time.sleep(1)

    print("✅ Preluare adaptivă completată!")

    # Mergem la poziția HOME
    print("→ Merg la poziția HOME ...")
    home()
    time.sleep(2)
    print("✅ Poziție HOME atinsă!")


if __name__ == "__main__":
    def print_menu():
        print("\n" + "=" * 40)
        print("MENIU AVNSAT BRACCIO")
        print("=" * 40)
        print("1. Poziția HOME")
        print("2. Rotire toate articulațiile")
        print("3. Deschide gripper")
        print("4. Închide gripper")
        print("5. Mergi la coordonate (x, y, z)")
        print("6. Pick Standard (preia și mută)")
        print("7. Pick Smooth (mișcare fluidă)")
        print("8. Pick Adaptiv (ajustare precisă)")
        print("9. Compensare cameră (x, y)")
        print("10. Test mișcare verticală")
        print("11. Test mișcare orizontală")
        print("12. Calibrare backlash")
        print("13. Ieșire")
        print("=" * 40)


    while True:
        print_menu()
        choice = input("Alege opțiunea (1-13): ").strip()

        if choice == '1':
            print("→ HOME …")
            home()
            time.sleep(2)

        elif choice == '2':
            print("→ Rotire toate articulațiile …")
            rotate_all_joints()
            time.sleep(2)

        elif choice == '3':
            print("→ Deschidem gripper …")
            open_gripper()
            time.sleep(2)

        elif choice == '4':
            print("→ Închidem gripper …")
            close_gripper()
            time.sleep(2)

        elif choice == '5':
            print("→ Mișcare carteziană …")
            try:
                x = float(input("   x (mm): ").strip())
                y = float(input("   y (mm): ").strip())
                z = float(input("   z (mm): ").strip())
                grip = input("   Gripper (open/closed) [closed]: ").strip().lower()
                if grip == "":
                    grip = "closed"
                elif grip not in ["open", "closed"]:
                    print("   ⚠️  Valoare invalidă pentru gripper, folosesc 'closed'")
                    grip = "closed"
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue
            print(f"   → Trimitem la ({x}, {y}, {z}), gripper {grip} …")
            go_to_coordinate(x, y, z, grip_position=grip)
            time.sleep(2)

        elif choice == '6':
            print("→ Pick Standard - Preluare cu ajustare pe distanță …")
            try:
                x = float(input("   x (mm) pentru preluare: ").strip())
                y = float(input("   y (mm) pentru preluare: ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue
            print(f"   → Folosesc pick() standard pentru ({x}, {y})")
            pick(x, y)

        elif choice == '7':
            print("→ Pick Smooth - Preluare cu mișcare fluidă …")
            try:
                x = float(input("   x (mm) pentru preluare: ").strip())
                y = float(input("   y (mm) pentru preluare: ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue
            print(f"   → Folosesc pick_smooth_v2() pentru ({x}, {y})")
            pick_smooth_v2(x, y)

        elif choice == '8':
            print("→ Pick Adaptiv - Preluare cu ajustare foarte precisă …")
            try:
                x = float(input("   x (mm) pentru preluare: ").strip())
                y = float(input("   y (mm) pentru preluare: ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue
            print(f"   → Folosesc pick_adaptive() pentru ({x}, {y})")
            pick_adaptive(x, y)

        elif choice == '9':
            print("→ Compensare coordonate cameră …")
            try:
                x_cam = float(input("   x camera (pixeli): ").strip())
                y_cam = float(input("   y camera (pixeli): ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue

            x_comp, y_comp = camera_compensation(x_cam, y_cam)
            print(f"   → Coordonate compensate: ({x_comp}, {y_comp})")

            action = input("   Vrei să mergi la aceste coordonate? (y/N): ").strip().lower()
            if action == 'y' or action == 'yes':
                print(f"   → Merg la coordonatele compensate ({x_comp}, {y_comp}, 0)")
                go_to_coordinate(x_comp, y_comp, 0, grip_position="closed")
                time.sleep(2)

        elif choice == '10':
            print("→ Test mișcare verticală …")
            try:
                x = float(input("   x fix (mm): ").strip())
                y = float(input("   y fix (mm): ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide.")
                continue
            print(f"   → Test vertical la poziția ({x}, {y})")
            move_vertical(x, y)
            time.sleep(2)

        elif choice == '11':
            print("→ Test mișcare orizontală …")
            try:
                z = float(input("   z fix (mm): ").strip())
            except ValueError:
                print("   ❌ Trebuie să introduci numere valide. ")
                continue
            print(f"   → Test orizontal la înălțimea z={z}")
            move_horizontal(z)
            time.sleep(2)

        elif choice == '12':
            print("→ Calibrare backlash …")
            confirm = input("   Acest test durează ~11 secunde. Continui? (y/N): ").strip().lower()
            if confirm == 'y' or confirm == 'yes':
                print("   → Încep calibrarea backlash …")
                backlash()
                print("   ✅ Calibrare backlash completă!")
            else:
                print("   → Calibrare anulată.")
            time.sleep(1)

        elif choice == '13':
            print("→ HOME și închidem portul serial …")
            home()
            time.sleep(2)
            arm.close()
            print("Port serial închis. Exiting.")
            break

        else:
            print("❌ Opțiune invalidă! Alege un număr între 1 și 13.")

    print("Program terminat. La revedere!")