import os
import psutil
import serial, serial.tools.list_ports

from logic.config_watcher import *
from logic.logger import logger

class ArduinoMouse:
    def __init__(self):
        self.cfg = Config()
        
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = self.cfg.arduino_baudrate
        self.serial_port.timeout = 0
        self.serial_port.write_timeout = 0
        
        if self.cfg.arduino_port == 'auto':
            self.serial_port.port = self.__detect_port()
        else:
            self.serial_port.port = self.cfg.arduino_port
        
        try:
            self.serial_port.open()
            logger.info(f'[Arduino] Connected! Port: {self.serial_port.port}')
        except Exception as e:
            logger.error(f'[Arduino] Not Connected...\n{e}')
            self.checks()

        if not self.serial_port.is_open:
            exit()
                    
    def click(self):
        self._send_command('c')

    def press(self):
        self._send_command('p')

    def release(self):
        self._send_command('r')
        
    def move(self, x, y):
        if self.cfg.arduino_16_bit_mouse:
            data = f'm{x},{y}\n'.encode()
            self.serial_port.write(data)
        else:
            x_parts = self._split_value(x)
            y_parts = self._split_value(y)
            for x_part, y_part in zip(x_parts, y_parts):
                data = f'm{x_part},{y_part}\n'.encode()
                self.serial_port.write(data)
        
    def _split_value(self, value):
        if value == 0:
            return [0]
        
        values = []
        sign = -1 if value < 0 else 1

        while abs(value) > 127:
            values.append(sign * 127)
            value -= sign * 127

        values.append(value)

        return values
    
    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()

    def __del__(self):
        self.close()

    def __detect_port(self):
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            if "Arduino" in port.description:
                return port.device
        return None

    def _send_command(self, command):
        self.serial_port.write(f'{command}\n'.encode())
    
    def find_library_directory(self, base_path, library_name_start):
        for root, dirs, files in os.walk(base_path):
            for dir_name in dirs:
                if dir_name.startswith(library_name_start):
                    return os.path.join(root, dir_name)
        return None

    def checks(self):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == 'Arduino IDE.exe':
                logger.error('[Arduino] Arduino IDE is open, close IDE and restart app.')
                break
        
        try:
            documents_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
            arduino_libraries_path = os.path.join(documents_path, 'Arduino', 'libraries')
            
            USB_Host_Shield_library_path = self.find_library_directory(arduino_libraries_path, 'USB_Host_Shield')
            if USB_Host_Shield_library_path is None:
                logger.error("[Arduino] Usb host shield library not found")
                return
            
            hid_settings = os.path.join(USB_Host_Shield_library_path, 'settings.h')
            
            if os.path.exists(hid_settings):
                with open(hid_settings, 'r') as file:
                    for line in file:
                        if line.startswith('#define ENABLE_UHS_DEBUGGING'):
                            parts = line.split()
                            if len(parts) == 3 and parts[1] == 'ENABLE_UHS_DEBUGGING':
                                value = parts[2]
                                if value == '1':
                                    logger.error(f'[Arduino] Disable `ENABLE_UHS_DEBUGGING` setting in {hid_settings} file.')
                                    break
        except Exception as e:
            logger.error(f'[Arduino] USB_Host_Shield lib not found.\n{e}')
            
arduino = ArduinoMouse()