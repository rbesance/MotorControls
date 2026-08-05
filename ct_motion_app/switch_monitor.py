"""
switch_monitor.py

Continuously polls limit and home switches on the DMC-4020 and prints
any state changes to the terminal. Press 'P' to stop.

Switch bits returned by the TS command:
    Bit 0 (1) — Home switch
    Bit 1 (2) — Reverse limit
    Bit 2 (4) — Forward limit
"""

import sys
import time
import threading

from galil_controller import GalilController
from config import CONTROLLER_ADDRESS

# Axes present on the DMC-4020 and their friendly names
AXES = {"A": "Z", "B": "Theta"}

# Bit masks for the TS command response
BIT_HOME    = 0b001  # bit 0
BIT_REVERSE = 0b010  # bit 1
BIT_FORWARD = 0b100  # bit 2

SWITCH_BITS = {
    "Home":         BIT_HOME,
    "Reverse Limit": BIT_REVERSE,
    "Forward Limit": BIT_FORWARD,
}

stop_event = threading.Event()


def _listen_for_p() -> None:
    """Block on stdin waiting for 'P'; set stop_event when pressed.

    Uses msvcrt on Windows (no Enter needed) and falls back to
    standard line-buffered input on Unix (requires Enter).
    """
    try:
        import msvcrt
        while not stop_event.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch.lower() == "p":
                    stop_event.set()
                    break
            time.sleep(0.05)
    except ImportError:
        # Unix fallback — requires pressing Enter after P
        for line in sys.stdin:
            if line.strip().lower() == "p":
                stop_event.set()
                break


def parse_switches(raw: int) -> dict[str, bool]:
    return {name: bool(raw & bit) for name, bit in SWITCH_BITS.items()}


def main() -> None:
    controller = GalilController(CONTROLLER_ADDRESS)
    controller.connect()
    print("Connected to DMC-4020. Monitoring switches — press P to stop.\n")

    key_thread = threading.Thread(target=_listen_for_p, daemon=True)
    key_thread.start()

    prev: dict[str, dict[str, bool]] = {axis: {} for axis in AXES}

    try:
        while not stop_event.is_set():
            for axis, label in AXES.items():
                raw = int(float(controller.command(f"TS{axis}")))
                current = parse_switches(raw)

                for switch, active in current.items():
                    was_active = prev[axis].get(switch, False)
                    if active and not was_active:
                        print(f"  [{label}]  {switch}  →  ACTIVE")
                    elif not active and was_active:
                        print(f"  [{label}]  {switch}  →  cleared")

                prev[axis] = current

            time.sleep(0.05)  # 20 Hz

    finally:
        controller.close()
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
