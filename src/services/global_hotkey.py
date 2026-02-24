from __future__ import annotations

import logging

import keyboard
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

_REFRESH_INTERVAL_MS = 5000


class GlobalHotkeyService(QObject):
    triggered = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl+`", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._registered = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_hook)

    def start(self) -> None:
        if self._registered:
            return
        try:
            keyboard.add_hotkey(self._hotkey, self._on_hotkey, suppress=True)
            self._registered = True
            self._refresh_timer.start(_REFRESH_INTERVAL_MS)
            logger.info("Global hotkey registered: %s", self._hotkey)
        except Exception:
            logger.exception("Failed to register global hotkey: %s", self._hotkey)

    def stop(self) -> None:
        self._refresh_timer.stop()
        if not self._registered:
            return
        try:
            keyboard.remove_hotkey(self._hotkey)
        except Exception:
            pass
        self._registered = False

    def update_hotkey(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()

    def _refresh_hook(self) -> None:
        """Re-register hotkey to recover from silent hook removal by Windows."""
        if not self._registered:
            return
        try:
            keyboard.remove_hotkey(self._hotkey)
        except Exception:
            pass
        try:
            keyboard.add_hotkey(self._hotkey, self._on_hotkey, suppress=True)
        except Exception:
            logger.warning("Failed to re-register global hotkey: %s", self._hotkey)

    def _on_hotkey(self) -> None:
        self.triggered.emit()
