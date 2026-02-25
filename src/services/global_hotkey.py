from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging

from PyQt6.QtCore import QAbstractNativeEventFilter, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32

# RegisterHotKey modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

_HOTKEY_ID = 0xBFFF  # arbitrary unique ID

# keyboard-library-style name → modifier flag
_MOD_MAP: dict[str, int] = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "alt": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

# keyboard-library-style name → virtual-key code
_VK_MAP: dict[str, int] = {
    "`": 0xC0, "~": 0xC0,
    "-": 0xBD, "=": 0xBB,
    "[": 0xDB, "]": 0xDD,
    "\\": 0xDC, ";": 0xBA,
    "'": 0xDE, ",": 0xBC,
    ".": 0xBE, "/": 0xBF,
    "space": 0x20, "enter": 0x0D, "return": 0x0D,
    "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    **{f"f{i}": 0x6F + i for i in range(1, 25)},  # F1=0x70 .. F24
}


def _parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """Parse a keyboard-library-style hotkey string into (modifiers, vk)."""
    parts = hotkey_str.lower().replace(" ", "").split("+")
    mods = MOD_NOREPEAT  # prevent auto-repeat flooding
    vk = 0
    for part in parts:
        if part in _MOD_MAP:
            mods |= _MOD_MAP[part]
        elif part in _VK_MAP:
            vk = _VK_MAP[part]
        elif len(part) == 1 and part.isalpha():
            vk = ord(part.upper())
        elif len(part) == 1 and part.isdigit():
            vk = ord(part)
    return mods, vk


class _HotkeyNativeFilter(QAbstractNativeEventFilter):
    """Catches WM_HOTKEY from the Windows message queue."""

    def __init__(self, hotkey_id: int, callback) -> None:
        super().__init__()
        self._hotkey_id = hotkey_id
        self._callback = callback

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            # message is a sip.voidptr → cast to MSG*
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
                self._callback()
                return True, 0
        return False, 0


class GlobalHotkeyService(QObject):
    """System-wide hotkey using Win32 RegisterHotKey.

    Unlike the keyboard-library approach, this does NOT install a
    WH_KEYBOARD_LL hook, so it cannot interfere with the numpad hook
    in numpad_hook.dll.
    """

    triggered = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl+`", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._registered = False
        self._filter: _HotkeyNativeFilter | None = None

    def start(self) -> None:
        if self._registered:
            return
        mods, vk = _parse_hotkey(self._hotkey)
        if vk == 0:
            logger.error("Could not parse hotkey: %s", self._hotkey)
            return

        ok = user32.RegisterHotKey(None, _HOTKEY_ID, mods, vk)
        if not ok:
            err = ctypes.GetLastError()
            logger.error("RegisterHotKey failed (err=%d): %s", err, self._hotkey)
            return

        self._registered = True

        # Install native event filter so Qt delivers WM_HOTKEY to us
        self._filter = _HotkeyNativeFilter(_HOTKEY_ID, self._on_hotkey)
        app = QApplication.instance()
        if app is not None:
            app.installNativeEventFilter(self._filter)

        logger.info("Global hotkey registered (RegisterHotKey): %s", self._hotkey)

    def stop(self) -> None:
        if not self._registered:
            return
        user32.UnregisterHotKey(None, _HOTKEY_ID)
        self._registered = False

        if self._filter is not None:
            app = QApplication.instance()
            if app is not None:
                app.removeNativeEventFilter(self._filter)
            self._filter = None

    def update_hotkey(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()

    def _on_hotkey(self) -> None:
        self.triggered.emit()
