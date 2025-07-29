import sys
import time

if sys.platform == "win32":
    import ctypes

    SendInput = ctypes.windll.user32.SendInput

    W = 0x11
    A = 0x1E
    S = 0x1F
    D = 0x20
    LeftArrow = 0x25
    RightArrow = 0x27
    Space = 0x39
    # C struct redefinitions
    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", PUL),
        ]

    class HardwareInput(ctypes.Structure):
        _fields_ = [
            ("uMsg", ctypes.c_ulong),
            ("wParamL", ctypes.c_short),
            ("wParamH", ctypes.c_ushort),
        ]

    class MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", PUL),
        ]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

    def PressKey(hexKeyCode):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        # Using wVk here (no SCANCODE flag!)
        ii_.ki = KeyBdInput(hexKeyCode, 0, 0x0000, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def ReleaseKey(hexKeyCode):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        # Add KEYEVENTF_KEYUP to dwFlags
        ii_.ki = KeyBdInput(hexKeyCode, 0, 0x0002, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

elif sys.platform == "darwin" or sys.platform.startswith("linux"): # macOS or Linux
    import pyautogui

    W = "w"
    A = "a"
    S = "s"
    D = "d"
    LeftArrow = "left"
    RightArrow = "right"
    Space = "space" 

    def PressKey(key):
        pyautogui.keyDown(key)

    def ReleaseKey(key):
        pyautogui.keyUp(key)

else:
    raise NotImplementedError(
        "This script is only implemented for Windows, macOS, and Linux."
    )

