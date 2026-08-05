"""
read_program.py

Reads the program currently stored in the DMC-4020's memory and prints
it to the terminal. Optionally saves it to a .dmc file for safe-keeping.

How program storage works on the DMC-4020:
    - RAM holds the active program (lost on power cycle).
    - Flash EEPROM holds the burned program (survives power cycles).
      A program is burned to EEPROM with the BP command.
    - If a program starts with the label #AUTO, the controller
      automatically executes it on every power-up or reset.

This script uses GProgramUpload(), which returns whatever is currently
in program memory (the EEPROM-burned program is loaded into RAM on boot,
so this captures it either way).
"""

import sys
from galil_controller import GalilController
from config import CONTROLLER_ADDRESS


def read_program(controller: GalilController) -> str:
    """Upload and return the program stored on the controller."""
    return controller.g.GProgramUpload()


def main() -> None:
    save_path = sys.argv[1] if len(sys.argv) > 1 else None

    controller = GalilController(CONTROLLER_ADDRESS)
    controller.connect()
    print("Connected to DMC-4020.\n")

    try:
        program = read_program(controller)

        if not program.strip():
            print("No program found in controller memory.")
        else:
            print("=== Program stored on controller ===\n")
            print(program)
            print("====================================\n")

            if save_path:
                with open(save_path, "w") as f:
                    f.write(program)
                print(f"Program saved to: {save_path}")
            else:
                print("Tip: pass a filename as an argument to save the program to disk.")
                print("     e.g.  python read_program.py backup.dmc")

    finally:
        controller.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
