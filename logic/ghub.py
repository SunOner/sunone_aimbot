from ctypes import *
from os import path

class GhubMouse:
    def __init__(self):
        self.basedir = path.dirname(path.abspath(__file__))
        self.dlldir = path.join(self.basedir, 'ghub_mouse.dll')
        self.gm = CDLL(self.dlldir)
        self.gmok = self.gm.mouse_open()

    @staticmethod
    def _ghub_SendInput(*inputs):
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = c_int(sizeof(INPUT))
        return windll.user32.SendInput(nInputs, pInputs, cbSize)

    @staticmethod
    def _ghub_Input(structure):
        return INPUT(0, _INPUTunion(mi=structure))

    @staticmethod
    def _ghub_MouseInput(flags, x, y, data):
        return MOUSEINPUT(x, y, data, flags, 0, None)

    @staticmethod
    def _ghub_Mouse(flags, x=0, y=0, data=0):
        return GhubMouse._ghub_Input(GhubMouse._ghub_MouseInput(flags, x, y, data))

    def mouse_xy(self, x, y):
        if self.gmok:
            return self.gm.moveR(x, y)
        return self._ghub_SendInput(self._ghub_Mouse(0x0001, x, y))

    def mouse_down(self, key=1):
        if self.gmok:
            return self.gm.press(key)
        if key == 1:
            return self._ghub_SendInput(self._ghub_Mouse(0x0002))
        elif key == 2:
            return self._ghub_SendInput(self._ghub_Mouse(0x0008))

    def mouse_up(self, key=1):
        if self.gmok:
            return self.gm.release()
        if key == 1:
            return self._ghub_SendInput(self._ghub_Mouse(0x0004))
        elif key == 2:
            return self._ghub_SendInput(self._ghub_Mouse(0x0010))

    def mouse_close(self):
        if self.gmok:
            return self.gm.mouse_close()

LONG = c_long
DWORD = c_ulong
ULONG_PTR = POINTER(DWORD)
            
class MOUSEINPUT(Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class _INPUTunion(Union):
    _fields_ = (('mi', MOUSEINPUT),)

class INPUT(Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))
    
gHub = GhubMouse()