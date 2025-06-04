# Adaugă această funcție corectată pentru poziția HOME
def home_position():
    """Mută robotul la poziția de acasă"""
    angle_string_def_angles = [base[0], shoulder[0], elbow[0], wrist[0], wristRot[0], gripper[0]]
    write_arduino(angle_string_def_angles)


# Adaugă acest cod la sfârșitul fișierului braccio_control_python.py

def test_all_joints():
    """Testează toate articulațiile la limitele lor cu pauze de 3 secunde"""
    print("=== ÎNCEPEREA TESTĂRII ARTICULAȚIILOR ===")
    delay = 3  # secunde

    # Pornește de la poziția home
    print("1. Mergem la poziția HOME...")
    home_position()
    time.sleep(delay)

    # Testare BAZĂ (BASE) - rotație stânga-dreapta
    print("\n2. Testare BAZĂ (BASE):")
    print("   - Poziția minimă (0°)")
    write_position(theta_base=0)
    time.sleep(delay)

    print("   - Poziția centrală (90°)")
    write_position(theta_base=90)
    time.sleep(delay)

    print("   - Poziția maximă (180°)")
    write_position(theta_base=180)
    time.sleep(delay)

    print("   - Înapoi la centru")
    write_position(theta_base=90)
    time.sleep(delay)

    # Testare UMĂR (SHOULDER)
    print("\n3. Testare UMĂR (SHOULDER):")
    print("   - Poziția minimă (15°)")
    write_position(theta_shoulder=15)
    time.sleep(delay)

    print("   - Poziția medie (90°)")
    write_position(theta_shoulder=90)
    time.sleep(delay)

    print("   - Poziția maximă (165°)")
    write_position(theta_shoulder=165)
    time.sleep(delay)

    print("   - Înapoi la default (150°)")
    write_position(theta_shoulder=150)
    time.sleep(delay)

    # Testare COT (ELBOW)
    print("\n4. Testare COT (ELBOW):")
    print("   - Poziția minimă (0°)")
    write_position(theta_elbow=0)
    time.sleep(delay)

    print("   - Poziția medie (90°)")
    write_position(theta_elbow=90)
    time.sleep(delay)

    print("   - Poziția maximă (180°)")
    write_position(theta_elbow=180)
    time.sleep(delay)

    print("   - Înapoi la default (0°)")
    write_position(theta_elbow=0)
    time.sleep(delay)

    # Testare ÎNCHEIETURĂ VERTICALĂ (WRIST)
    print("\n5. Testare ÎNCHEIETURĂ VERTICALĂ (WRIST):")
    print("   - Poziția minimă (0°)")
    write_position(theta_wrist=0)
    time.sleep(delay)

    print("   - Poziția medie (90°)")
    write_position(theta_wrist=90)
    time.sleep(delay)

    print("   - Poziția maximă (180°)")
    write_position(theta_wrist=180)
    time.sleep(delay)

    print("   - Înapoi la default (0°)")
    write_position(theta_wrist=0)
    time.sleep(delay)

    # Testare ROTAȚIE ÎNCHEIETURĂ (WRIST ROTATION)
    print("\n6. Testare ROTAȚIE ÎNCHEIETURĂ (WRIST ROTATION):")
    print("   - Poziția minimă (0°)")
    write_position(theta_wristRot=0)
    time.sleep(delay)

    print("   - Poziția default (90°)")
    write_position(theta_wristRot=90)
    time.sleep(delay)

    print("   - Poziția maximă (180°)")
    write_position(theta_wristRot=180)
    time.sleep(delay)

    print("   - Înapoi la default (90°)")
    write_position(theta_wristRot=90)
    time.sleep(delay)

    # Testare CLEȘTE (GRIPPER)
    print("\n7. Testare CLEȘTE (GRIPPER):")
    print("   - Deschis complet")
    open_gripper()
    time.sleep(delay)

    print("   - Închis complet")
    close_gripper()
    time.sleep(delay)

    print("   - Deschis din nou")
    open_gripper()
    time.sleep(delay)

    print("   - Închis din nou")
    close_gripper()
    time.sleep(delay)

    # Întoarcere la poziția home
    print("\n8. Întoarcere la poziția HOME...")
    home_position()
    time.sleep(delay)

    print("\n=== TESTAREA COMPLETĂ! ===")


def test_sequence_movements():
    """Testează o secvență de mișcări combinate"""
    print("\n=== TESTARE SECVENȚĂ MIȘCĂRI COMBINATE ===")
    delay = 3

    positions = [
        {"name": "Poziția 1 - Stânga sus", "base": 45, "shoulder": 45, "elbow": 45, "wrist": 45},
        {"name": "Poziția 2 - Centru jos", "base": 90, "shoulder": 120, "elbow": 120, "wrist": 90},
        {"name": "Poziția 3 - Dreapta sus", "base": 135, "shoulder": 60, "elbow": 60, "wrist": 120},
        {"name": "Poziția 4 - Întins înainte", "base": 90, "shoulder": 90, "elbow": 0, "wrist": 90},
    ]

    for pos in positions:
        print(f"   - {pos['name']}")
        write_position(
            theta_base=pos['base'],
            theta_shoulder=pos['shoulder'],
            theta_elbow=pos['elbow'],
            theta_wrist=pos['wrist']
        )
        time.sleep(delay)

    print("   - Înapoi la HOME")
    home_position()
    time.sleep(delay)

    print("=== SECVENȚA COMPLETĂ! ===")


def interactive_test_menu():
    """Meniu interactiv pentru testare"""
    while True:
        print("\n" + "=" * 50)
        print("MENIU TESTARE BRACCIO ROBOT")
        print("=" * 50)
        print("1. Testare completă toate articulațiile")
        print("2. Testare secvență mișcări combinate")
        print("3. Testare articulație individuală")
        print("4. Poziția HOME")
        print("5. Deschide cleștele")
        print("6. Închide cleștele")
        print("7. Ieșire")
        print("=" * 50)

        choice = input("Alege opțiunea (1-7): ").strip()

        try:
            if choice == '1':
                test_all_joints()
            elif choice == '2':
                test_sequence_movements()
            elif choice == '3':
                test_individual_joint()
            elif choice == '4':
                print("Mergem la poziția HOME...")
                home_position()
                time.sleep(2)
            elif choice == '5':
                print("Deschidem cleștele...")
                open_gripper()
                time.sleep(2)
            elif choice == '6':
                print("Închidem cleștele...")
                close_gripper()
                time.sleep(2)
            elif choice == '7':
                print("Închiderea programului...")
                break
            else:
                print("Opțiune invalidă! Încearcă din nou.")

        except Exception as e:
            print(f"Eroare: {e}")
            print("Continuăm...")


def test_individual_joint():
    """Testează o articulație individuală"""
    print("\nTestare articulație individuală:")
    print("1. Bază (BASE)")
    print("2. Umăr (SHOULDER)")
    print("3. Cot (ELBOW)")
    print("4. Încheietură (WRIST)")
    print("5. Rotație încheietură (WRIST ROT)")

    joint_choice = input("Alege articulația (1-5): ").strip()

    if joint_choice == '1':
        print("Testare BAZĂ...")
        for angle in [0, 45, 90, 135, 180, 90]:
            print(f"   - Unghi: {angle}°")
            write_position(theta_base=angle)
            time.sleep(3)
    elif joint_choice == '2':
        print("Testare UMĂR...")
        for angle in [15, 60, 90, 120, 165, 150]:
            print(f"   - Unghi: {angle}°")
            write_position(theta_shoulder=angle)
            time.sleep(3)
    elif joint_choice == '3':
        print("Testare COT...")
        for angle in [0, 45, 90, 135, 180, 0]:
            print(f"   - Unghi: {angle}°")
            write_position(theta_elbow=angle)
            time.sleep(3)
    elif joint_choice == '4':
        print("Testare ÎNCHEIETURĂ...")
        for angle in [0, 45, 90, 135, 180, 0]:
            print(f"   - Unghi: {angle}°")
            write_position(theta_wrist=angle)
            time.sleep(3)
    elif joint_choice == '5':
        print("Testare ROTAȚIE ÎNCHEIETURĂ...")
        for angle in [0, 45, 90, 135, 180, 90]:
            print(f"   - Unghi: {angle}°")
            write_position(theta_wristRot=angle)
            time.sleep(3)
    else:
        print("Opțiune invalidă!")


# Cod principal pentru executare
if __name__ == "__main__":
    try:
        print("BRACCIO ROBOT - SISTEM DE TESTARE")
        print("Robotul este inițializat și gata pentru testare!")

        # Rulează meniul interactiv
        interactive_test_menu()

    except KeyboardInterrupt:
        print("\nProgram întrerupt de utilizator")
    except Exception as e:
        print(f"Eroare: {e}")
    finally:
        print("Închiderea conexiunii cu robotul...")
        arm.close()
        print("Gata!")