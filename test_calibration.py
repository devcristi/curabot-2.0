from braccio_control_a4 import a4_to_robot_coords, move_to_a4_position
import time


def test_real_coordinates():
    """
    Testează coordonatele reale cu robotul.
    Setup: 4 foi A4 în peisaj (landscape), cu centrul la 20cm lățime și 30cm lungime.

    Dimensiuni foaie A4 în peisaj: 297mm x 210mm
    4 foi A4 în peisaj: 594mm lățime x 420mm lungime
    Centrul real: 200mm lățime, 300mm lungime
    """

    # Dimensiuni reale setup
    real_width = 594  # mm (2 foi A4 pe lățime)
    real_height = 420  # mm (2 foi A4 pe lungime)

    # Centrul real măsurat de tine: 20cm lățime, 30cm lungime
    real_center_x = 200  # mm (20cm)
    real_center_y = 300  # mm (30cm)

    # Puncte de test
    test_points = [
        ("Centru Real", (real_center_x, real_center_y)),
        ("Colț Stânga Sus", (0, 0)),
        ("Colț Dreapta Sus", (real_width, 0)),
        ("Colț Stânga Jos", (0, real_height)),
        ("Colț Dreapta Jos", (real_width, real_height)),
        ("Centru Teoretic", (real_width / 2, real_height / 2))
    ]

    z_height = 100  # mm înălțime de lucru

    print("=== TEST COORDONATE REALE ===")
    print(f"Setup: {real_width}mm x {real_height}mm")
    print(f"Centru real măsurat: ({real_center_x}, {real_center_y})")
    print()

    # Afișează coordonatele calculate
    for name, (a4_x, a4_y) in test_points:
        robot_coords = a4_to_robot_coords(a4_x, a4_y, z_height)
        print(f"{name}: A4({a4_x}, {a4_y}) -> Robot{robot_coords}")

    print("\n" + "=" * 50)

    # Testare cu robotul (deblochează pentru mișcare reală)
    test_with_robot = input("Dorești să testezi cu robotul? (y/n): ").lower() == 'y'

    if test_with_robot:
        print("\n=== TESTARE CU ROBOTUL ===")
        print("ATENȚIE: Robotul se va mișca! Asigură-te că zona este liberă.")

        # Testează punctele importante
        important_points = [
            ("Centru Real", (real_center_x, real_center_y)),
            ("Centru Teoretic", (real_width / 2, real_height / 2))
        ]

        for name, (a4_x, a4_y) in important_points:
            input(f"\nApasă ENTER pentru a merge la {name}...")

            print(f"Mergând la {name}: A4({a4_x}, {a4_y})")
            try:
                move_to_a4_position(a4_x, a4_y, z_height, grip="open")
                print(f"Robotul ar trebui să fie la {name}")

                # Pauză pentru observare
                time.sleep(2)

            except Exception as e:
                print(f"Eroare la deplasarea către {name}: {e}")

        print("\nTest finalizat!")
    else:
        print("Test doar cu coordonate, fără mișcare robot.")


def calibrate_center():
    """
    Funcție pentru calibrarea centrului.
    Folosește această funcție pentru a verifica dacă coordonatele calculate
    corespund cu poziția reală a robotului.
    """
    print("=== CALIBRARE CENTRU ===")

    # Coordonatele centrului real măsurat
    real_center_x = 200  # 20cm
    real_center_y = 300  # 30cm
    z_height = 100

    print(f"Centru real: ({real_center_x}, {real_center_y})")

    robot_coords = a4_to_robot_coords(real_center_x, real_center_y, z_height)
    print(f"Coordonate robot calculate: {robot_coords}")

    test_move = input("Testezi mișcarea la centru? (y/n): ").lower() == 'y'

    if test_move:
        print("Deplasare la centrul real...")
        try:
            move_to_a4_position(real_center_x, real_center_y, z_height, grip="open")
            print("Robotul ar trebui să fie la centrul real al foilor!")

            # Verifică dacă poziția este corectă
            feedback = input("Este robotul la centrul corect? (y/n): ").lower()
            if feedback == 'y':
                print("✅ Calibrarea este corectă!")
            else:
                print("❌ Calibrarea necesită ajustări în funcția a4_to_robot_coords()")

        except Exception as e:
            print(f"Eroare: {e}")


if __name__ == "__main__":
    print("Alege opțiunea:")
    print("1. Test coordonate reale")
    print("2. Calibrare centru")

    choice = input("Opțiunea (1/2): ")

    if choice == "1":
        test_real_coordinates()
    elif choice == "2":
        calibrate_center()
    else:
        print("Opțiune invalidă!")