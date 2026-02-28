from __future__ import annotations

import os
import sys
from typing import Any

# action type → icon filename (without extension)
# media_control uses per-command sub-icons, so excluded here
ACTION_ICON_MAP: dict[str, str] = {
    "launch_app": "launch_app",
    "hotkey": "hotkey",
    "text_input": "text_input",
    "system_monitor": "system_monitor",
    "navigate_folder": "navigate_folder",
    "open_url": "open_url",
    "macro": "macro",
    "run_command": "run_command",
}

# media_control command → sub-icon filename
MEDIA_ICON_MAP: dict[str, str] = {
    "play_pause": "play_pause",
    "next_track": "next_track",
    "prev_track": "prev_track",
    "stop": "stop",
    "volume_up": "volume_up",
    "volume_down": "volume_down",
    "mute": "mute",
}


def _icons_dir() -> str:
    """Return the absolute path to the default action icons directory."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", "icons", "actions")


def _find_icon(directory: str, name: str) -> str:
    """Try .png / .svg / .ico in directory. Return path or empty."""
    for ext in (".png", ".svg", ".ico"):
        path = os.path.join(directory, name + ext)
        if os.path.isfile(path):
            return path
    return ""


def get_default_icon_path(action_type: str, params: dict[str, Any] | None = None) -> str:
    """Return the icon file path for an action type, or empty string if not found."""
    icons = _icons_dir()

    if action_type == "media_control" and params:
        command = params.get("command", "")
        filename = MEDIA_ICON_MAP.get(command, "")
        if filename:
            return _find_icon(os.path.join(icons, "media_control"), filename)
        return ""

    filename = ACTION_ICON_MAP.get(action_type, "")
    if not filename:
        return ""
    return _find_icon(icons, filename)
