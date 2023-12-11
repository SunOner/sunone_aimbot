import random
import time
import serial
import serial.tools.list_ports
import asyncio

class ArduinoMouse:
    def __init__(self, filter_length=3):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 115200
        self.serial_port.timeout = 1
        self.serial_port.port = self.find_serial_port()
        self.filter_length = filter_length
        self.x_history = [0] * filter_length
        self.y_history = [0] * filter_length
        try:
            self.serial_port.open()
        except serial.SerialException:
            print('Serial port in use by another app..')
            time.sleep(10)
            exit()

    def find_serial_port(self):
        port = next((port for port in serial.tools.list_ports.comports() if "Arduino" in port.description), None)
        if port is not None:
            return port.device
        else:
            print('Unable to find serial port or the Arduino device is with different name. Please check its connection and try again.')
            time.sleep(10)
            exit()

    async def move(self, x, y):
        self.x_history.append(x)
        self.y_history.append(y)

        self.x_history.pop(0)
        self.y_history.pop(0)

        smooth_x = int(sum(self.x_history) / self.filter_length)
        smooth_y = int(sum(self.y_history) / self.filter_length)

        finalx = smooth_x + 256 if smooth_x < 0 else smooth_x
        finaly = smooth_y + 256 if smooth_y < 0 else smooth_y
        try:
            self.serial_port.write(b"M" + bytes([int(finalx), int(finaly)]))
        except: pass
        
    def flick(self, x, y):
        x = x + 256 if x < 0 else x
        y = y + 256 if y < 0 else y
        self.serial_port.write(b"M" + bytes([int(x), int(y)]))
        
    async def click(self):
        self.serial_port.write(b"C")
        
    def close(self):
        self.serial_port.close()

    def __del__(self):
        self.close()