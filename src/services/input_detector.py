from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import threading

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

LLKHF_INJECTED = 0x00000010
LLKHF_EXTENDED = 0x00000001
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_TIMER = 0x0113
VK_NUMLOCK = 0x90

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ---------- Win32 API type declarations (64-bit safe) ----------

# CallNextHookEx
user32.CallNextHookEx.argtypes = [
    ctypes.wintypes.HHOOK,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
user32.CallNextHookEx.restype = ctypes.wintypes.LPARAM

# SetWindowsHookExW — returns HHOOK (pointer-sized, 64-bit on x64)
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,             # idHook
    ctypes.c_void_p,          # lpfn (HOOKPROC)
    ctypes.wintypes.HINSTANCE,  # hMod
    ctypes.wintypes.DWORD,    # dwThreadId
]
user32.SetWindowsHookExW.restype = ctypes.wintypes.HHOOK

# UnhookWindowsHookEx
user32.UnhookWindowsHookEx.argtypes = [ctypes.wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL

# UINT_PTR: pointer-sized unsigned integer (64-bit on x64)
UINT_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint

# SetTimer — returns UINT_PTR (64-bit on x64); without this, the
# default c_int (32-bit) truncates the timer ID, making it impossible
# to match against WM_TIMER wParam and the rehook timer never fires.
user32.SetTimer.argtypes = [
    ctypes.wintypes.HWND,
    UINT_PTR,
    ctypes.wintypes.UINT,
    ctypes.c_void_p,          # TIMERPROC (NULL for WM_TIMER)
]
user32.SetTimer.restype = UINT_PTR

# KillTimer
user32.KillTimer.argtypes = [ctypes.wintypes.HWND, UINT_PTR]
user32.KillTimer.restype = ctypes.wintypes.BOOL

# GetModuleHandleW
kernel32.GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = ctypes.wintypes.HMODULE

# Module handle of current process — needed for SetWindowsHookExW
_hmod = kernel32.GetModuleHandleW(None)

# HOOKPROC: must use LPARAM (pointer-sized) for return and lParam
HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.wintypes.LPARAM,  # return
    ctypes.c_int,            # nCode
    ctypes.wintypes.WPARAM,  # wParam
    ctypes.wintypes.LPARAM,  # lParam
)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _NumpadSignal(QObject):
    """Bridge to emit numpad presses from the hook thread to the Qt main thread."""
    pressed = pyqtSignal(int, int)
    back_pressed = pyqtSignal()
    numlock_changed = pyqtSignal(bool)  # True = Num Lock ON, False = OFF


class InputDetector:
    """Tracks injected keys and provides global numpad shortcuts (Num Lock OFF only)."""

    # When Num Lock is OFF, numpad keys send navigation VK codes WITHOUT the extended flag.
    # Regular arrow/Home/End keys send the SAME VK codes but WITH the extended flag.
    _NUMPAD_MAP: dict[int, tuple[int, int]] = {
        0x24: (0, 0),  # VK_HOME   → numpad 7
        0x26: (0, 1),  # VK_UP     → numpad 8
        0x21: (0, 2),  # VK_PRIOR  → numpad 9
        0x25: (1, 0),  # VK_LEFT   → numpad 4
        0x0C: (1, 1),  # VK_CLEAR  → numpad 5
        0x27: (1, 2),  # VK_RIGHT  → numpad 6
        0x23: (2, 0),  # VK_END    → numpad 1
        0x28: (2, 1),  # VK_DOWN   → numpad 2
        0x22: (2, 2),  # VK_NEXT   → numpad 3
    }

    _POLL_MS = 50  # Single timer interval for polling + hook health
    _REHOOK_TICKS = 20  # Reinstall hook every 20 ticks (= ~1 second)

    def __init__(self) -> None:
        self._last_injected = False
        self._hook = None
        self._timer_id = 0
        self._tick_count = 0
        self._thread: threading.Thread | None = None
        self._running = False
        self._passthrough = False
        self._proc = HOOKPROC(self._hook_proc)
        self.numpad_signal = _NumpadSignal()
        self._last_numlock_state: bool | None = None

    def set_passthrough(self, value: bool) -> None:
        """When True, numpad keys pass through to the active window (for dialogs)."""
        self._passthrough = value

    @property
    def last_was_injected(self) -> bool:
        return self._last_injected

    @staticmethod
    def is_numlock_on() -> bool:
        """Return True if Num Lock is currently active."""
        return bool(user32.GetKeyState(VK_NUMLOCK) & 1)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            thread_id = self._thread.ident
            if thread_id:
                user32.PostThreadMessageW(thread_id, 0x0012, 0, 0)
            self._thread.join(timeout=2)

    def _is_numpad_zero(self, kb: KBDLLHOOKSTRUCT) -> bool:
        """Check if key is numpad 0 (VK_INSERT when Num Lock OFF, non-extended)."""
        if kb.flags & LLKHF_INJECTED:
            return False
        if kb.flags & LLKHF_EXTENDED:
            return False
        if user32.GetKeyState(VK_NUMLOCK) & 1:
            return False
        return kb.vkCode == 0x2D  # VK_INSERT

    def _is_numpad_nav_key(self, kb: KBDLLHOOKSTRUCT) -> tuple[int, int] | None:
        """Check if key is a numpad navigation key (Num Lock OFF, non-extended, non-injected)."""
        if kb.flags & LLKHF_INJECTED:
            return None
        if kb.flags & LLKHF_EXTENDED:
            return None
        if user32.GetKeyState(VK_NUMLOCK) & 1:
            return None
        return self._NUMPAD_MAP.get(kb.vkCode)

    def _hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self._last_injected = bool(kb.flags & LLKHF_INJECTED)

                # Detect Num Lock toggle
                if kb.vkCode == VK_NUMLOCK:
                    # Hook fires before state flips, so invert current state
                    will_be_on = not bool(user32.GetKeyState(VK_NUMLOCK) & 1)
                    self._last_numlock_state = will_be_on
                    self.numpad_signal.numlock_changed.emit(will_be_on)

                if not self._passthrough:
                    pos = self._is_numpad_nav_key(kb)
                    if pos is not None:
                        self.numpad_signal.pressed.emit(pos[0], pos[1])
                        return 1  # suppress

                    # Numpad 0 (VK_INSERT when Num Lock OFF, non-extended)
                    if self._is_numpad_zero(kb):
                        self.numpad_signal.back_pressed.emit()
                        return 1

            elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                if not self._passthrough:
                    # Suppress matching key-up to avoid orphan events
                    if self._is_numpad_nav_key(kb) is not None:
                        return 1
                    if self._is_numpad_zero(kb):
                        return 1

        return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def _on_tick(self) -> None:
        """Called every 50ms: poll Num Lock + periodically reinstall hook."""
        # Always poll Num Lock state (catches missed hook events)
        current = bool(user32.GetKeyState(VK_NUMLOCK) & 1)
        if current != self._last_numlock_state:
            self._last_numlock_state = current
            self.numpad_signal.numlock_changed.emit(current)

        # Reinstall hook every ~1 second (20 ticks × 50ms)
        self._tick_count += 1
        if self._tick_count >= self._REHOOK_TICKS:
            self._tick_count = 0
            self._reinstall_hook()

    def _reinstall_hook(self) -> None:
        """Reinstall keyboard hook to recover from silent removal by Windows.

        Windows removes WH_KEYBOARD_LL hooks if the callback doesn't return
        within LowLevelHooksTimeout (~300ms). This can happen when the Python
        GIL is held by the main thread (e.g. during heavy UI rendering on
        multi-monitor setups with different DPI scaling).
        """
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, _hmod, 0
        )
        if not self._hook:
            logger.warning("Failed to reinstall keyboard hook")
        else:
            logger.debug("Keyboard hook reinstalled successfully")

    def _run(self) -> None:
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, _hmod, 0
        )
        if not self._hook:
            logger.error("Failed to install keyboard hook")
            return
        logger.info("InputDetector hook installed")

        # Initialize last known Num Lock state
        self._last_numlock_state = bool(user32.GetKeyState(VK_NUMLOCK) & 1)

        # Single 50ms timer handles both Num Lock polling and periodic hook reinstall
        self._timer_id = int(user32.SetTimer(None, 0, self._POLL_MS, None))
        self._tick_count = 0

        logger.info("InputDetector timer started (id=%s, interval=%dms)", self._timer_id, self._POLL_MS)

        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            if msg.message == WM_TIMER and int(msg.wParam) == self._timer_id:
                self._on_tick()
                continue
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._timer_id:
            user32.KillTimer(None, self._timer_id)
            self._timer_id = 0
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        logger.info("InputDetector hook removed")
