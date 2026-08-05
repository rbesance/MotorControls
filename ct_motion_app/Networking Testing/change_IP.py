import serial
import time
s = serial.Serial("COM4", baudrate=115200, timeout=2, rtscts=True) 
s.write(b"IA 192,168,42,100\r")  # or whatever address you want 
time.sleep(0.1) 
s.write(b"IH 192,168,42,1\r") # gateway — your PC's IP 
time.sleep(0.1) 
s.write(b"BN\r") # burn to EEPROM
