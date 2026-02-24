from __future__ import annotations

import logging
import webbrowser
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class OpenUrlAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        url = params.get("url", "")
        if not url:
            logger.warning("open_url: no url specified")
            return

        try:
            webbrowser.open(url)
            logger.info("Opened URL: %s", url)
        except Exception:
            logger.exception("Failed to open URL: %s", url)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
