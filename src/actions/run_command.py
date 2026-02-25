from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class RunCommandAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        command = params.get("command", "")
        working_dir = params.get("working_dir", "")
        show_window = params.get("show_window", True)

        if not command:
            logger.warning("run_command: no command specified")
            return

        try:
            kwargs: dict[str, Any] = {"shell": True}
            if not show_window:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            else:
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
            if working_dir and os.path.isdir(working_dir):
                kwargs["cwd"] = working_dir
            subprocess.Popen(command, **kwargs)
            logger.info("Executed command: %s", command)
        except Exception:
            logger.exception("Failed to execute command: %s", command)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
