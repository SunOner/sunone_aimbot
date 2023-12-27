import threading
import serial
import serial.tools.list_ports
import time

def split_value(value):
    MAX_VALUE = 127
    values = []

    sign = -1 if value < 0 else 1

    while abs(value) > MAX_VALUE:
        values.append(sign * MAX_VALUE)
        value -= sign * MAX_VALUE

    values.append(value)

    return values

class ArduinoMouse:
    def __init__(self):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 9600
        self.serial_port.timeout = 0
        self.serial_port.write_timeout = 0
        self.serial_port.port = self.__detect_port()
        # self.mouse_is_pressed = False

        try:
            self.serial_port.open()
            print('Arduino: Connected!')
        except:
            serial.SerialException('Arduino: Device not found. Enter (mode) in cmd and check devices.')

        if not self.serial_port.is_open:
            print('Arduino: Not connected.')
            time.sleep(4)
            exit()

        # serial_reader = threading.Thread(target = self.__read_buffer)
        # serial_reader.daemon = True
        # serial_reader.start()

    # def __read_buffer(self):
    #     while True:
    #         line = self.serial_port.readline()
    #         if line != b'':
    #             if 112 in line:
    #                 self.mouse_pressed = True
    #             if 113 in line:
    #                 self.mouse_pressed = False
    
    def click(self):
        self.serial_port.write(b'c')
        self.serial_port.write(b'\n')

    def press(self):
        self.serial_port.write(b'p')
        self.serial_port.write(b'\n')

    def release(self):
        self.serial_port.write(b'r')
        self.serial_port.write(b'\n')

    def move(self, x, y):
        x_parts = split_value(x)
        y_parts = split_value(y)
        for x, y in zip(x_parts, y_parts):
            data = str('m{},{}'.format((int(x)), (int(y))))
            data = str.encode(data)
            self.serial_port.write(data)
        self.serial_port.write(b'\n')
        
    def close(self):
        self.serial_port.close()

    def __del__(self):
        self.close()

    def __detect_port(self):
        ports = serial.tools.list_ports.comports()
        arduino_port = None

        for port in ports:
            if "Arduino" in port[1]:
                arduino_port = port[0]

        return arduino_port