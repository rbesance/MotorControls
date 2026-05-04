import gclib

g = gclib.py()

try:
    g.GOpen("192.168.42.54")
    print("Connected!")
    print(g.GInfo())
    print("TPA:", g.GCommand("TPA"))
finally:
    g.GClose()