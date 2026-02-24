from __future__ import annotations

import logging
from typing import Any

import keyboard

from .base import ActionBase

logger = logging.getLogger(__name__)


class HotkeyAction(ActionBase):
    # Hotkeys that Windows blocks from keyboard simulation — handled via direct API calls
    _SPECIAL_HOTKEYS: dict[str, object] = {}

    @classmethod
    def _init_special(cls) -> None:
        if cls._SPECIAL_HOTKEYS:
            return
        import ctypes
        cls._SPECIAL_HOTKEYS = {
            "win+l": lambda: ctypes.windll.user32.LockWorkStation(),
        }

    def execute(self, params: dict[str, Any]) -> None:
        keys = params.get("keys", "")
        if not keys:
            logger.warning("hotkey: no keys specified")
            return

        try:
            self._init_special()
            handler = self._SPECIAL_HOTKEYS.get(keys.lower().replace(" ", ""))
            if handler:
                handler()
            else:
                keyboard.send(keys)
            logger.info("Sent hotkey: %s", keys)
        except Exception:
            logger.exception("Failed to send hotkey: %s", keys)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
