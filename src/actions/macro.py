from __future__ import annotations

import logging
import threading
import time
from typing import Any

import keyboard

from .base import ActionBase

logger = logging.getLogger(__name__)


def _resolve_pynput_key(key_name: str, vk: int) -> Any:
    """Resolve a recorded key name + vk code to a pynput Key or KeyCode."""
    from pynput.keyboard import Key, KeyCode

    # Try named key first (e.g. 'shift', 'ctrl_l', 'space')
    try:
        return Key[key_name]
    except (KeyError, ValueError):
        pass

    # Single character
    if len(key_name) == 1:
        return KeyCode.from_char(key_name)

    # vk-based fallback
    if vk:
        return KeyCode.from_vk(vk)

    return None


def _resolve_mouse_button(name: str) -> Any:
    """Resolve a button name to a pynput mouse.Button."""
    from pynput.mouse import Button

    return getattr(Button, name, Button.left)


class MacroAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        steps = params.get("steps", [])
        if not steps:
            logger.warning("macro: no steps defined")
            return

        threading.Thread(target=self._run_steps, args=(steps,), daemon=True).start()

    def _run_steps(self, steps: list[dict[str, Any]]) -> None:
        for i, step in enumerate(steps):
            step_type = step.get("type", "")
            step_params = step.get("params", {})
            try:
                if step_type == "hotkey":
                    keys = step_params.get("keys", "")
                    if keys:
                        keyboard.send(keys)
                        logger.info("Macro step %d: sent hotkey %s", i, keys)
                elif step_type == "text_input":
                    text = step_params.get("text", "")
                    if text:
                        if step_params.get("use_clipboard", False):
                            self._paste_via_clipboard(text)
                        else:
                            keyboard.write(text, delay=0.02)
                        logger.info("Macro step %d: text input (%d chars)", i, len(text))
                elif step_type == "delay":
                    ms = step_params.get("ms", 100)
                    time.sleep(ms / 1000)
                    logger.info("Macro step %d: delay %dms", i, ms)
                elif step_type == "key_down":
                    self._do_key_down(step_params)
                    logger.info("Macro step %d: key_down %s", i, step_params.get("key"))
                elif step_type == "key_up":
                    self._do_key_up(step_params)
                    logger.info("Macro step %d: key_up %s", i, step_params.get("key"))
                elif step_type == "mouse_down":
                    self._do_mouse_down(step_params)
                    logger.info("Macro step %d: mouse_down %s @ (%s,%s)", i,
                                step_params.get("button"), step_params.get("x"), step_params.get("y"))
                elif step_type == "mouse_up":
                    self._do_mouse_up(step_params)
                    logger.info("Macro step %d: mouse_up %s @ (%s,%s)", i,
                                step_params.get("button"), step_params.get("x"), step_params.get("y"))
                elif step_type == "mouse_scroll":
                    self._do_mouse_scroll(step_params)
                    logger.info("Macro step %d: mouse_scroll @ (%s,%s) d(%s,%s)", i,
                                step_params.get("x"), step_params.get("y"),
                                step_params.get("dx"), step_params.get("dy"))
                else:
                    logger.warning("Macro step %d: unknown type '%s'", i, step_type)
            except Exception:
                logger.exception("Macro step %d failed (type=%s)", i, step_type)

    @staticmethod
    def _paste_via_clipboard(text: str) -> None:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
        keyboard.send("ctrl+v")

    @staticmethod
    def _do_key_down(params: dict[str, Any]) -> None:
        from pynput.keyboard import Controller
        key = _resolve_pynput_key(params.get("key", ""), params.get("vk", 0))
        if key is not None:
            Controller().press(key)

    @staticmethod
    def _do_key_up(params: dict[str, Any]) -> None:
        from pynput.keyboard import Controller
        key = _resolve_pynput_key(params.get("key", ""), params.get("vk", 0))
        if key is not None:
            Controller().release(key)

    @staticmethod
    def _do_mouse_down(params: dict[str, Any]) -> None:
        from pynput.mouse import Controller
        mc = Controller()
        mc.position = (params.get("x", 0), params.get("y", 0))
        mc.press(_resolve_mouse_button(params.get("button", "left")))

    @staticmethod
    def _do_mouse_up(params: dict[str, Any]) -> None:
        from pynput.mouse import Controller
        mc = Controller()
        mc.position = (params.get("x", 0), params.get("y", 0))
        mc.release(_resolve_mouse_button(params.get("button", "left")))

    @staticmethod
    def _do_mouse_scroll(params: dict[str, Any]) -> None:
        from pynput.mouse import Controller
        mc = Controller()
        mc.position = (params.get("x", 0), params.get("y", 0))
        mc.scroll(params.get("dx", 0), params.get("dy", 0))

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        steps = params.get("steps", [])
        if not steps:
            return None
        return f"Macro ({len(steps)} steps)"
