import serial 
s = serial.Serial("COM4", baudrate=115200, timeout=2, rtscts=True) 
s.write(b"TH\r") 
print(s.read(100)) 
s.close()
