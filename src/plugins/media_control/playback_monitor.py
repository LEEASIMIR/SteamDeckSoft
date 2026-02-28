from __future__ import annotations

import asyncio
import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# WinRT SMTC availability flag
_HAS_WINRT = False
_HAS_STREAMS = False
try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    _HAS_WINRT = True
except Exception:
    logger.debug("winrt not available — media playback monitoring disabled")

try:
    from winrt.windows.storage.streams import DataReader
    _HAS_STREAMS = True
except Exception:
    logger.debug("winrt.windows.storage.streams not available — thumbnail disabled")


def _poll_smtc() -> tuple[bool | None, str, bytes]:
    """Return (is_playing, track_info, thumbnail_bytes) from SMTC.

    is_playing: True if playing, False if paused/stopped, None if unavailable.
    track_info: "Artist\\nTitle" or "" if unavailable.
    thumbnail_bytes: raw image bytes or b"" if unavailable.
    """
    if not _HAS_WINRT:
        return None, "", b""
    try:
        loop = asyncio.new_event_loop()
        try:
            manager = loop.run_until_complete(
                SessionManager.request_async()
            )
            session = manager.get_current_session()
            if session is None:
                return False, "", b""

            info = session.get_playback_info()
            is_playing = info.playback_status == PlaybackStatus.PLAYING

            track_info = ""
            thumbnail_bytes = b""
            try:
                props = loop.run_until_complete(
                    session.try_get_media_properties_async()
                )
                artist = props.artist or ""
                title = props.title or ""
                if title:
                    track_info = f"{artist}\n{title}" if artist else title

                # Read thumbnail
                if _HAS_STREAMS and props.thumbnail is not None:
                    try:
                        stream = loop.run_until_complete(
                            props.thumbnail.open_read_async()
                        )
                        size = stream.size
                        if size > 0:
                            reader = DataReader(stream)
                            loop.run_until_complete(reader.load_async(size))
                            buf = bytearray(size)
                            reader.read_bytes(buf)
                            thumbnail_bytes = bytes(buf)
                    except Exception:
                        logger.debug("Failed to read thumbnail", exc_info=True)
            except Exception:
                logger.debug("Failed to get media properties", exc_info=True)

            return is_playing, track_info, thumbnail_bytes
        finally:
            loop.close()
    except Exception:
        logger.debug("Failed to query playback status", exc_info=True)
        return None, "", b""


class MediaPlaybackMonitor(QThread):
    """Polls Windows SMTC for media playback state changes."""

    playback_state_changed = pyqtSignal(bool)  # True = playing
    track_info_changed = pyqtSignal(str, object)  # (text, thumbnail_bytes)

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True
        self._last_state: bool | None = None
        self._last_track: str = ""

    @property
    def available(self) -> bool:
        return _HAS_WINRT

    def run(self) -> None:
        if not _HAS_WINRT:
            return

        while self._running:
            state, track_info, thumbnail = _poll_smtc()
            if state is not None and state != self._last_state:
                self._last_state = state
                self.playback_state_changed.emit(state)
            if track_info != self._last_track:
                self._last_track = track_info
                self.track_info_changed.emit(track_info, thumbnail)
            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait(3000)
