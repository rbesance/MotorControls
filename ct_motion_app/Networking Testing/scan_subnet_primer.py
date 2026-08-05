"""
scan_subnet.py

Scans the 192.168.42.x subnet for Galil controllers by attempting a
gclib connection to each address. Runs in parallel for speed.

Usage:
    python scan_subnet.py              # scans 192.168.42.1-254
    python scan_subnet.py 192.168.1    # scans a different subnet
"""

import sys
import socket
import gclib
import threading

SUBNET      = sys.argv[1] if len(sys.argv) > 1 else "192.168.42"
START       = 1
END         = 254
SOCKET_TIMEOUT = 0.5   # seconds for TCP probe
GALIL_PORT  = 23       # Telnet port Galil controllers listen on
MAX_THREADS = 50       # probe 50 addresses at a time

found = []
found_lock = threading.Lock()


def is_host_alive(ip: str) -> bool:
    """Quick TCP probe to check if anything is listening on the Galil port."""
    try:
        with socket.create_connection((ip, GALIL_PORT), timeout=SOCKET_TIMEOUT):
            return True
    except OSError:
        return False


def try_connect(ip: str) -> None:
    """Only attempt gclib connection if the host responds to a TCP probe."""
    if not is_host_alive(ip):
        return
    g = gclib.py()
    try:
        g.GOpen(ip)
        info = g.GCommand("TH")
        with found_lock:
            found.append((ip, info.strip()))
        g.GClose()
    except Exception:
        pass


def warmup_gclib() -> None:
    """gclib requires an initial connection before subsequent connections
    work reliably. Calling GAddresses() is enough to initialize its
    internal state without needing a known controller address."""
    try:
        gclib.py().GAddresses()
    except Exception:
        pass


def main() -> None:
    addresses = [f"{SUBNET}.{i}" for i in range(START, END + 1)]
    total = len(addresses)

    print("Initializing gclib...")
    warmup_gclib()
    print(f"Scanning {SUBNET}.{START}–{END} ({total} addresses)...\n")

    # Process in batches to cap active threads
    for batch_start in range(0, total, MAX_THREADS):
        batch = addresses[batch_start:batch_start + MAX_THREADS]
        threads = [threading.Thread(target=try_connect, args=(ip,)) for ip in batch]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        progress = min(batch_start + MAX_THREADS, total)
        print(f"  Checked {progress}/{total}...", end="\r")

    print()

    if found:
        print(f"\nFound {len(found)} Galil controller(s):")
        for ip, info in found:
            print(f"  {ip}")
            print(f"    {info}")
        print("\nUpdate CONTROLLER_ADDRESS in config.py with the correct IP.")
    else:
        print("No Galil controllers found on this subnet.")
        print("Check that the controller is powered on and connected to the network.")


if __name__ == "__main__":
    main()
