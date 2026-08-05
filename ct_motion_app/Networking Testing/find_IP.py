import gclib
g = gclib.py()
g.GOpen("COM3 --baud 115200")
print(g.GCommand("TH"))