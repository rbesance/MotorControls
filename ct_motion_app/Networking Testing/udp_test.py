# this script tests if the UDP socket on this computer works

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(2)
s.sendto(b"\x00", ("255.255.255.255", 60007))
try:
    data, addr = s.recvfrom(1024)
    print(f"Response from {addr}: {data}")
except socket.timeout:
    print("No response — firewall is likely blocking UDP 60007")
finally:
    s.close()