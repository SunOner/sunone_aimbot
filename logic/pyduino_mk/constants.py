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

# Mouse basic commands and arguments
MOUSE_CMD            = 0xE0
MOUSE_CALIBRATE      = 0xE1
MOUSE_PRESS          = 0xE2
MOUSE_RELEASE        = 0xE3

MOUSE_CLICK          = 0xE4
MOUSE_FAST_CLICK     = 0xE5
MOUSE_MOVE           = 0xE6
MOUSE_BEZIER         = 0xE7

# Mouse buttons
MOUSE_LEFT           = 0xEA
MOUSE_RIGHT          = 0xEB
MOUSE_MIDDLE         = 0xEC
MOUSE_BUTTONS        = [MOUSE_LEFT,
                        MOUSE_MIDDLE,
                        MOUSE_RIGHT]

# Keyboard commands and arguments
KEYBOARD_CMD         = 0xF0
KEYBOARD_PRESS       = 0xF1
KEYBOARD_RELEASE     = 0xF2
KEYBOARD_RELEASE_ALL = 0xF3
KEYBOARD_PRINT       = 0xF4
KEYBOARD_PRINTLN     = 0xF5
KEYBOARD_WRITE       = 0xF6
KEYBOARD_TYPE        = 0xF7

# Arduino keyboard modifiers
# http://arduino.cc/en/Reference/KeyboardModifiers
LEFT_CTRL            = 0x80
LEFT_SHIFT           = 0x81
LEFT_ALT             = 0x82
LEFT_GUI             = 0x83
RIGHT_CTRL           = 0x84
RIGHT_SHIFT          = 0x85
RIGHT_ALT            = 0x86
RIGHT_GUI            = 0x87
UP_ARROW             = 0xDA
DOWN_ARROW           = 0xD9
LEFT_ARROW           = 0xD8
RIGHT_ARROW          = 0xD7
BACKSPACE            = 0xB2
TAB                  = 0xB3
RETURN               = 0xB0
ESC                  = 0xB1
INSERT               = 0xD1
DELETE               = 0xD4
PAGE_UP              = 0xD3
PAGE_DOWN            = 0xD6
HOME                 = 0xD2
END                  = 0xD5
CAPS_LOCK            = 0xC1
F1                   = 0xC2
F2                   = 0xC3
F3                   = 0xC4
F4                   = 0xC5
F5                   = 0xC6
F6                   = 0xC7
F7                   = 0xC8
F8                   = 0xC9
F9                   = 0xCA
F10                  = 0xCB
F11                  = 0xCC
F12                  = 0xCD

# etc.
SCREEN_CALIBRATE     = 0xFF
COMMAND_COMPLETE     = 0xFE
