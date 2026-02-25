from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import os
import subprocess
import sys
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

VK_NUMLOCK = 0x90
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Setup argtypes for shared memory APIs
kernel32.OpenFileMappingW.argtypes = [
    ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.LPCWSTR,
]
kernel32.OpenFileMappingW.restype = ctypes.wintypes.HANDLE

kernel32.MapViewOfFile.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.c_size_t,
]
kernel32.MapViewOfFile.restype = ctypes.c_void_p

kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
kernel32.UnmapViewOfFile.restype = ctypes.wintypes.BOOL

kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

SHM_NAME = "Local\\SteamDeckSoft_NumpadHook"
FILE_MAP_ALL_ACCESS = 0x000F001F
MAX_EVENTS = 256


class _SharedData(ctypes.Structure):
    """Must match the C struct in numpad_hook.c exactly."""
    _pack_ = 1
    _fields_ = [
        ("ev_write",      ctypes.c_long),
        ("ev_read",       ctypes.c_long),
        ("events",        ctypes.c_int * MAX_EVENTS),
        ("nl_changed",    ctypes.c_long),
        ("nl_new_state",  ctypes.c_int),
        ("passthrough",   ctypes.c_int),
        ("numlock_off",   ctypes.c_int),
        ("running",       ctypes.c_int),
        ("any_key_count", ctypes.c_long),
        ("suppressed",    ctypes.c_long),
        ("numpad_seen",   ctypes.c_long),
        ("hook_ok",       ctypes.c_long),
    ]


class _NumpadSignal(QObject):
    pressed = pyqtSignal(int, int)
    back_pressed = pyqtSignal()
    numlock_changed = pyqtSignal(bool)


def _find_hook_dll() -> str:
    """Locate numpad_hook.dll next to the exe or in src/native/."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    candidates = [
        os.path.join(base, "numpad_hook.dll"),
        os.path.join(base, "..", "native", "numpad_hook.dll"),
        os.path.join(base, "native", "numpad_hook.dll"),
    ]
    for p in candidates:
        norm = os.path.normpath(p)
        if os.path.isfile(norm):
            return norm
    raise FileNotFoundError(
        f"numpad_hook.dll not found in: {[os.path.normpath(c) for c in candidates]}"
    )


class InputDetector:
    """Numpad key capture using rundll32.exe hosting our C hook DLL.

    rundll32.exe (a trusted Windows system binary) loads numpad_hook.dll
    in a separate process — completely independent of Python/PyInstaller.
    The DLL installs a WH_KEYBOARD_LL hook and communicates events via
    a named shared-memory region that we poll via QTimer.
    """

    _NUMPAD_SCAN_MAP: dict[int, tuple[int, int]] = {
        71: (0, 0), 72: (0, 1), 73: (0, 2),
        75: (1, 0), 76: (1, 1), 77: (1, 2),
        79: (2, 0), 80: (2, 1), 81: (2, 2),
    }
    _NUMPAD_BACK_SCAN = 82

    _POLL_INTERVAL_MS = 16  # ~60 Hz

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._shm_ptr: int = 0  # raw address for UnmapViewOfFile
        self._shm: _SharedData | None = None
        self._hMap = None
        self._poll_timer: QTimer | None = None
        self._debug_timer: QTimer | None = None
        self.numpad_signal = _NumpadSignal()

    # -- public API -------------------------------------------------------

    def set_passthrough(self, value: bool) -> None:
        if self._shm is not None:
            self._shm.passthrough = 1 if value else 0

    @property
    def last_was_injected(self) -> bool:
        return False

    @staticmethod
    def is_numlock_on() -> bool:
        return bool(user32.GetKeyState(VK_NUMLOCK) & 1)

    def start(self) -> None:
        dll_path = _find_hook_dll()
        logger.info("Starting hook via rundll32: %s", dll_path)

        # Launch rundll32.exe hosting our hook DLL (hidden window)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        # rundll32 syntax: rundll32.exe "path\to.dll",EntryPoint [args]
        # Pass our PID so the DLL exits if we crash.
        self._proc = subprocess.Popen(
            f'rundll32.exe "{dll_path}",start_entry {os.getpid()}',
            startupinfo=si,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # Wait for the process to create shared memory
        self._hMap = None
        for _ in range(100):  # up to 1s
            self._hMap = kernel32.OpenFileMappingW(
                FILE_MAP_ALL_ACCESS, False, SHM_NAME,
            )
            if self._hMap:
                break
            time.sleep(0.01)

        if not self._hMap:
            logger.error("Failed to open shared memory — hook process may have crashed")
            self._kill_proc()
            return

        self._shm_ptr = kernel32.MapViewOfFile(
            self._hMap, FILE_MAP_ALL_ACCESS, 0, 0, ctypes.sizeof(_SharedData),
        )
        if not self._shm_ptr:
            logger.error("MapViewOfFile failed")
            kernel32.CloseHandle(self._hMap)
            self._hMap = None
            self._kill_proc()
            return

        self._shm = _SharedData.from_address(self._shm_ptr)
        logger.info(
            "InputDetector started (rundll32, pid=%d, hook_ok=%d)",
            self._proc.pid, self._shm.hook_ok,
        )

        # Start polling
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(self._POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start()

        self._debug_timer = QTimer()
        self._debug_timer.setInterval(3000)
        self._debug_timer.timeout.connect(self._debug_log)
        self._debug_timer.start()

    def stop(self) -> None:
        if self._debug_timer is not None:
            self._debug_timer.stop()
            self._debug_timer = None
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

        # Tell the helper process to exit gracefully
        if self._shm is not None:
            self._shm.running = 0

        # Cleanup shared memory
        if self._shm_ptr:
            kernel32.UnmapViewOfFile(self._shm_ptr)
            self._shm_ptr = 0
            self._shm = None
        if self._hMap:
            kernel32.CloseHandle(self._hMap)
            self._hMap = None

        self._kill_proc()
        logger.info("InputDetector stopped")

    # -- internals --------------------------------------------------------

    def _kill_proc(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def _poll(self) -> None:
        shm = self._shm
        if shm is None:
            return

        # Drain ring buffer (we are the only consumer — no atomics needed)
        for _ in range(MAX_EVENTS):
            r = shm.ev_read
            if r == shm.ev_write:
                break
            scan = shm.events[r]
            shm.ev_read = (r + 1) % MAX_EVENTS

            pos = self._NUMPAD_SCAN_MAP.get(scan)
            if pos is not None:
                self.numpad_signal.pressed.emit(pos[0], pos[1])
            elif scan == self._NUMPAD_BACK_SCAN:
                self.numpad_signal.back_pressed.emit()

        # Num Lock change
        if shm.nl_changed:
            shm.nl_changed = 0
            is_on = bool(shm.nl_new_state)
            logger.info("Num Lock changed: %s", "ON" if is_on else "OFF")
            self.numpad_signal.numlock_changed.emit(is_on)

    def _debug_log(self) -> None:
        shm = self._shm
        if shm is None:
            return
        logger.info(
            "Hook process: hook=%d any_keys=%d numpad_seen=%d "
            "suppressed=%d numlock_off=%d",
            shm.hook_ok, shm.any_key_count, shm.numpad_seen,
            shm.suppressed, shm.numlock_off,
        )
