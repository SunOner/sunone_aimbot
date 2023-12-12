#!/usr/bin/env python

# Copyright (c) 2015 Nelson Tran
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import struct
import threading

import serial
import serial.tools.list_ports
from win32api import GetCursorPos, GetSystemMetrics

from logic.pyduino_mk.constants import *


class Arduino(object):
    def __init__(self, port=None, baudrate=115200):
        """
		Args:
		  port (str, optional): Device name or port number number or None.
		  baudrate (str, optional): Baud rate such as 9600 or 115200 etc.

		Raises:
		  SerialException: In the case the device cannot be found.

		Note:
		  You should not have to specify any arguments when instantiating
		  this class. The default parameters should work out of the box.
		
		  However, if the constructor is unable to automatically identify
		  the Arduino device, a port name should be explicitly specified.
		
		  If you specify a baud rate other than the default 115200 baud, you 
		  must modify the arduino sketch to match the specified baud rate.
		"""

        if port is None:
            port = self.__detect_port()

        self.serial = serial.Serial(port, baudrate)
        if not self.serial.isOpen():
            raise serial.SerialException("Arduino device not found.")

        # this flag denoting whether a command is has been completed
        # all module calls are blocking until the Arduino command is complete
        self.__command_complete = threading.Event()

        # read and parse bytes from the serial buffer
        serial_reader = threading.Thread(target=self.__read_buffer)
        serial_reader.daemon = True
        serial_reader.start()

    def press(self, button=MOUSE_LEFT):
        if button in MOUSE_BUTTONS:
            self.__write_byte(MOUSE_CMD)
            self.__write_byte(MOUSE_PRESS)
            self.__write_byte(button)

        elif isinstance(button, int):
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_PRESS)
            self.__write_byte(button)

        elif isinstance(button, str) and len(button) == 1:
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_PRESS)
            self.__write_byte(ord(button))

        else:
            raise ValueError("Not a valid mouse or keyboard button.")

        self.__command_complete.wait()

    def release(self, button=MOUSE_LEFT):
        if button in MOUSE_BUTTONS:
            self.__write_byte(MOUSE_CMD)
            self.__write_byte(MOUSE_RELEASE)
            self.__write_byte(button)

        elif isinstance(button, int):
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_RELEASE)
            self.__write_byte(button)

        elif isinstance(button, str) and len(button) == 1:
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_RELEASE)
            self.__write_byte(ord(button))

        else:
            raise ValueError("Not a valid mouse or keyboard button.")

        self.__command_complete.wait()

    def release_all(self):
        self.__write_byte(KEYBOARD_CMD)
        self.__write_byte(KEYBOARD_RELEASE_ALL)

        self.__command_complete.wait()

    def write(self, keys, endl=False):
        if isinstance(keys, int):
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_WRITE)
            self.__write_byte(keys)

        elif isinstance(keys, str) and len(keys) == 1:
            self.__write_byte(KEYBOARD_CMD)
            self.__write_byte(KEYBOARD_WRITE)
            self.__write_byte(ord(keys))

        elif isinstance(keys, str):
            if not endl:
                self.__write_byte(KEYBOARD_CMD)
                self.__write_byte(KEYBOARD_PRINT)
                self.__write_str(keys)
            else:
                self.__write_byte(KEYBOARD_CMD)
                self.__write_byte(KEYBOARD_PRINTLN)
                self.__write_str(keys)

        else:
            raise ValueError(
                "Not a valid keyboard keystroke. "
                + "Must be type `int` or `char` or `str`."
            )

        self.__command_complete.wait()

    def type(self, message, wpm=80, mistakes=True, accuracy=96):
        if not isinstance(message, str):
            raise ValueError("Invalid keyboard message. " + "Must be type `str`.")

        if not isinstance(wpm, int) and wpm < 1 or wpm > 255:
            raise ValueError(
                "Invalid value for `WPM`. " + "Must be type `int`: 1 <= WPM <= 255."
            )

        if not isinstance(mistakes, bool):
            raise ValueError("Invalid value for `mistakes`. " + "Must be type `bool`.")

        if not isinstance(accuracy, int) and accuracy < 1 or accuracy > 100:
            raise ValueError(
                "Invalid value for `accuracy`. "
                + "Must be type `int`: 1 <= accuracy <= 100."
            )

        self.__write_byte(KEYBOARD_CMD)
        self.__write_byte(KEYBOARD_TYPE)
        self.__write_str(message)
        self.__write_byte(wpm)
        self.__write_byte(mistakes)
        self.__write_byte(accuracy)

        self.__command_complete.wait()

    def click(self, button=MOUSE_LEFT):
        if button not in MOUSE_BUTTONS:
            raise ValueError("Not a valid mouse button.")

        self.__write_byte(MOUSE_CMD)
        self.__write_byte(MOUSE_CLICK)
        self.__write_byte(button)

        self.__command_complete.wait()

    def fast_click(self, button):
        if button not in MOUSE_BUTTONS:
            raise ValueError("Not a valid mouse button.")

        self.__write_byte(MOUSE_CMD)
        self.__write_byte(MOUSE_FAST_CLICK)
        self.__write_byte(button)

        self.__command_complete.wait()

    def move(self, dest_x, dest_y):
        if not isinstance(dest_x, (int, float)) and not isinstance(
            dest_y, (int, float)
        ):
            raise ValueError(
                "Invalid mouse coordinates. " + "Must be type `int` or `float`."
            )

        self.__write_byte(MOUSE_CMD)
        self.__write_byte(MOUSE_MOVE)
        self.__write_short(dest_x)
        self.__write_short(dest_y)

        self.__command_complete.wait()

    def bezier_move(self, dest_x, dest_y):
        if not isinstance(dest_x, (int, float)) and not isinstance(
            dest_y, (int, float)
        ):
            raise ValueError(
                "Invalid mouse coordinates. " + "Must be `int` or `float`."
            )

        self.__write_byte(MOUSE_CMD)
        self.__write_byte(MOUSE_BEZIER)
        self.__write_short(dest_x)
        self.__write_short(dest_y)

        self.__command_complete.wait()

    def close(self):
        self.serial.close()
        return True

    def __detect_port(self):
        ports = serial.tools.list_ports.comports()
        arduino_port = None

        for port in ports:
            if "Arduino" in port[1]:
                arduino_port = port[0]

        return arduino_port

    def __read_buffer(self):
        while True:
            byte = ord(self.serial.read())

            if byte == MOUSE_CALIBRATE:
                self.__calibrate_mouse()

            elif byte == SCREEN_CALIBRATE:
                self.__calibrate_screen()

            elif byte == COMMAND_COMPLETE:
                self.__command_complete.set()
                self.__command_complete.clear()

    def __calibrate_screen(self):
        width, height = GetSystemMetrics(0), GetSystemMetrics(1)

        self.__write_short(width)
        self.__write_short(height)

    def __calibrate_mouse(self):
        x, y = GetCursorPos()

        self.__write_short(x)
        self.__write_short(y)

    def __write_str(self, string):
        for char in string:
            self.__write_byte(ord(char))
        self.__write_byte(0x00)

    def __write_byte(self, byte):
        struct_pack = struct.pack("<B", byte)
        self.serial.write(struct_pack)

    def __write_short(self, short):
        struct_pack = struct.pack("<H", int(short))
        self.serial.write(struct_pack)
