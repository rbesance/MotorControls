"""
discover_controllers.py

Discovers Galil controllers on the local network and prints their addresses.

Two methods are tried in order:
    1. gclib.GAddresses() — uses gclib's built-in UDP discovery (preferred).
    2. Raw UDP broadcast — manual fallback if GAddresses() returns nothing.

Galil controllers listen on UDP port 60007 and respond to a broadcast
with their identity string, which includes their IP address.

Usage:
    python discover_controllers.py
"""

import socket
import gclib

GALIL_UDP_PORT = 60007
BROADCAST_ADDR = "255.255.255.255"
TIMEOUT_SEC    = 2


def discover_via_gclib() -> list[str]:
    """Use gclib's built-in discovery to find controllers.

    GAddresses() returns a dict keyed by address in the Python bindings,
    e.g. {"192.168.42.54": "DMC4020 Rev 1.3 ..."}
    """
    g = gclib.py()
    try:
        result = g.GAddresses()
        print(f"  DEBUG raw result: {result!r}")
        if isinstance(result, dict):
            return [f"{addr}  —  {info}".strip() for addr, info in result.items()]
        # Older versions may return a newline-delimited string
        return [a.strip() for a in result.strip().splitlines() if a.strip()]
    except Exception as e:
        print(f"  GAddresses() failed: {e}")
        return []


def discover_via_udp() -> list[str]:
    """Broadcast a UDP packet and collect responses from Galil controllers."""
    found = []

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(TIMEOUT_SEC)

    try:
        sock.sendto(b"\x00", (BROADCAST_ADDR, GALIL_UDP_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = data.decode("ascii", errors="ignore").strip()
                entry = f"{addr[0]}  —  {response}" if response else addr[0]
                if entry not in found:
                    found.append(entry)
            except socket.timeout:
                break
    finally:
        sock.close()

    return found


def main() -> None:
    print("Searching for Galil controllers on the network...\n")

 #  print("Method 1: gclib GAddresses()")
 #  addresses = discover_via_gclib()

   if addresses:
      print(f"  Found {len(addresses)} controller(s):")
       for a in addresses:
           print(f"    {a}")
   else:
        print("  Nothing found. Trying raw UDP broadcast...\n")

    print("Method 2: UDP broadcast")
    addresses = discover_via_udp()

    if addresses:
        print(f"  Found {len(addresses)} controller(s):")
        for a in addresses:
            print(f"    {a}")
    else:
        print("  Nothing found.")
        print("\n  Troubleshooting tips:")
        print("  - Make sure the controller is powered on and connected to the network.")
        print("  - Make sure your PC and the controller are on the same subnet.")
        print("  - Check that UDP port 60007 is not blocked by a firewall.")
        return

print("\nTo use a discovered address, update CONTROLLER_ADDRESS in config.py.")


if __name__ == "__main__":
    main()
