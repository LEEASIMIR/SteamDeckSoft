from __future__ import annotations

import logging
import os
import sys
import winreg

logger = logging.getLogger(__name__)

_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "SoftDeck"


def _get_launch_command() -> str:
    """Build the command string for the registry value."""
    exe = sys.executable
    # Prefer pythonw.exe to avoid a console window on startup
    if os.path.basename(exe).lower() == "python.exe":
        pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(pythonw):
            exe = pythonw

    main_py = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "main.py")
    )
    return f'"{exe}" "{main_py}"'


def set_autostart(enabled: bool) -> None:
    """Register or unregister SoftDeck in Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        try:
            if enabled:
                winreg.SetValueEx(
                    key, _VALUE_NAME, 0, winreg.REG_SZ, _get_launch_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
    except OSError:
        logger.exception("Failed to update autostart registry")


def is_autostart_enabled() -> bool:
    """Check whether SoftDeck is registered in Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False
