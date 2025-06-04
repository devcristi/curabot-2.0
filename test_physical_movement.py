from braccio_control_a4 import move_to_a4_position
import time


def test_movement():
    # Pentru testul fizic, vom folosi coordonate reprezentative din zona definită cu 4 foi A4.
    # În acest exemplu, presupunem că atribuim:
    #   - a4_x: coordonata pe lățime din sistemul A4 (în mm)
    #   - a4_y: coordonata pe înălțime din sistemul A4 (în mm)
    #   - z: înălțimea la care dorim să poziționăm brațul (ex: 100 mm)
    #
    # ATENȚIE: Asigură-te că zona de testare este liberă
    # și că mișcarea robotului nu va cauza coliziuni.

    # Exemplu: testăm mișcarea către centrul zonei (coordonatele sunt conform sistemului A4 definit)
    a4_x = 297.0  # coordonata din sistemul A4 (ajustează conform calibrării tale)
    a4_y = 210.0  # coordonata din sistemul A4
    z = 100  # înălțimea (mm) la care dorim să plasăm brațul

    print("Test fizic: Mișcare către poziția calculată...")
    move_to_a4_position(a4_x, a4_y, z, grip="closed")
    print("Mișcarea a fost trimisă către robot.")


if __name__ == "__main__":
    test_movement()
    # Adaugă o întârziere finală pentru a observa ultima mișcare, dacă este necesară.
    time.sleep(5)