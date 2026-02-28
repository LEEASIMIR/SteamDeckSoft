from __future__ import annotations

import logging
import time
from typing import Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

# Minimum delay threshold in seconds — delays below this are ignored
_MIN_DELAY_S = 0.005

# Control keys: F9 = stop, Escape = cancel
_STOP_VK = 120   # F9
_CANCEL_VK = 27  # Escape


class _RecorderSignals(QObject):
    event_recorded = pyqtSignal(int)       # event count
    recording_stopped = pyqtSignal(list)   # list of step dicts
    recording_cancelled = pyqtSignal()


class MacroRecorder:
    """Records keyboard and mouse events using pynput listeners."""

    def __init__(self) -> None:
        self.signals = _RecorderSignals()
        self._events: list[dict[str, Any]] = []
        self._last_time: float = 0.0
        self._kb_listener: Any = None
        self._mouse_listener: Any = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return

        from pynput import keyboard, mouse

        self._events = []
        self._last_time = time.perf_counter()
        self._running = True

        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )

        self._kb_listener.start()
        self._mouse_listener.start()
        logger.info("Macro recording started")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_listeners()
        steps = self._build_steps()
        logger.info("Macro recording stopped: %d steps", len(steps))
        self.signals.recording_stopped.emit(steps)

    def cancel(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_listeners()
        self._events.clear()
        logger.info("Macro recording cancelled")
        self.signals.recording_cancelled.emit()

    def _stop_listeners(self) -> None:
        if self._kb_listener is not None:
            self._kb_listener.stop()
            self._kb_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    # --- pynput callbacks (called from background threads) ---

    def _on_key_press(self, key: Any) -> None:
        if not self._running:
            return

        vk = self._get_vk(key)

        # F9 → stop recording (don't record this key)
        if vk == _STOP_VK:
            QTimer.singleShot(0, self.stop)
            return

        # Escape → cancel recording
        if vk == _CANCEL_VK:
            QTimer.singleShot(0, self.cancel)
            return

        self._append_delay()
        key_name = self._key_to_str(key)
        self._events.append({
            "type": "key_down",
            "params": {"key": key_name, "vk": vk},
        })
        self._emit_count()

    def _on_key_release(self, key: Any) -> None:
        if not self._running:
            return

        vk = self._get_vk(key)
        if vk in (_STOP_VK, _CANCEL_VK):
            return

        self._append_delay()
        key_name = self._key_to_str(key)
        self._events.append({
            "type": "key_up",
            "params": {"key": key_name, "vk": vk},
        })
        self._emit_count()

    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        if not self._running:
            return

        self._append_delay()
        btn_name = button.name  # 'left', 'right', 'middle'
        if pressed:
            self._events.append({
                "type": "mouse_down",
                "params": {"button": btn_name, "x": x, "y": y},
            })
        else:
            self._events.append({
                "type": "mouse_up",
                "params": {"button": btn_name, "x": x, "y": y},
            })
        self._emit_count()

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._running:
            return

        self._append_delay()
        self._events.append({
            "type": "mouse_scroll",
            "params": {"x": x, "y": y, "dx": dx, "dy": dy},
        })
        self._emit_count()

    # --- helpers ---

    def _append_delay(self) -> None:
        now = time.perf_counter()
        delta = now - self._last_time
        self._last_time = now
        if delta >= _MIN_DELAY_S:
            ms = round(delta * 1000)
            self._events.append({"type": "delay", "params": {"ms": ms}})

    def _emit_count(self) -> None:
        count = sum(1 for e in self._events if e["type"] != "delay")
        QTimer.singleShot(0, lambda c=count: self.signals.event_recorded.emit(c))

    def _build_steps(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self._events]

    @staticmethod
    def _get_vk(key: Any) -> int:
        """Extract virtual key code from a pynput key."""
        if hasattr(key, "vk") and key.vk is not None:
            return key.vk
        if hasattr(key, "value") and hasattr(key.value, "vk"):
            return key.value.vk
        return 0

    @staticmethod
    def _key_to_str(key: Any) -> str:
        """Convert a pynput key to a human-readable string."""
        from pynput.keyboard import Key

        if isinstance(key, Key):
            return key.name  # e.g. 'shift', 'ctrl_l', 'alt_l', 'space', etc.
        # KeyCode with char
        if hasattr(key, "char") and key.char is not None:
            return key.char
        # KeyCode without char — use vk
        vk = 0
        if hasattr(key, "vk") and key.vk is not None:
            vk = key.vk
        return f"<{vk}>"
