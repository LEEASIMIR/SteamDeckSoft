from __future__ import annotations

import logging
import os
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class OpenFolderAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        path = params.get("path", "")
        if not path:
            logger.warning("open_folder: no path specified")
            return

        path = os.path.expandvars(os.path.expanduser(path))
        if not os.path.isdir(path):
            logger.warning("open_folder: path is not a directory: %s", path)
            return

        try:
            os.startfile(path)
            logger.info("Opened folder: %s", path)
        except Exception:
            logger.exception("Failed to open folder: %s", path)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
