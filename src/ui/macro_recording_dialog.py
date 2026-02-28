from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

if TYPE_CHECKING:
    from ..services.macro_recorder import MacroRecorder


class MacroRecordingDialog(QDialog):
    """Floating overlay shown during macro recording."""

    def __init__(self, recorder: MacroRecorder, parent=None) -> None:
        super().__init__(parent)
        self._recorder = recorder
        self._start_time = time.monotonic()
        self._event_count = 0
        self._result_steps: list[dict] | None = None

        self.setWindowTitle("Macro Recording")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setFixedWidth(280)

        self._build_ui()
        self._connect_signals()

        # Elapsed time updater
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._timer.start(200)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Resolve theme accent color
        accent = "#e94560"
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, '_theme'):
                accent = widget._theme.palette.accent
                break
            widget = getattr(widget, 'parent', lambda: None)()

        self._status_label = QLabel("Recording...")
        self._status_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {accent};"
        )
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        self._count_label = QLabel("Events: 0")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_label)

        self._time_label = QLabel("Elapsed: 0.0s")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._time_label)

        hint_label = QLabel("F9 = Stop  |  Esc = Cancel")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint_label)

        btn_row = QHBoxLayout()
        self._stop_btn = QPushButton("Stop (F9)")
        self._stop_btn.clicked.connect(self._on_stop)
        btn_row.addWidget(self._stop_btn)

        self._cancel_btn = QPushButton("Cancel (Esc)")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

    def _connect_signals(self) -> None:
        self._recorder.signals.event_recorded.connect(self._on_event_recorded)
        self._recorder.signals.recording_stopped.connect(self._on_recording_stopped)
        self._recorder.signals.recording_cancelled.connect(self._on_recording_cancelled)

    def _on_event_recorded(self, count: int) -> None:
        self._event_count = count
        self._count_label.setText(f"Events: {count}")

    def _on_recording_stopped(self, steps: list[dict]) -> None:
        self._timer.stop()
        self._result_steps = steps
        self.accept()

    def _on_recording_cancelled(self) -> None:
        self._timer.stop()
        self._result_steps = None
        self.reject()

    def _on_stop(self) -> None:
        self._recorder.stop()

    def _on_cancel(self) -> None:
        self._recorder.cancel()

    def _update_elapsed(self) -> None:
        elapsed = time.monotonic() - self._start_time
        self._time_label.setText(f"Elapsed: {elapsed:.1f}s")

    def get_recorded_steps(self) -> list[dict] | None:
        """Return recorded steps after dialog closes, or None if cancelled."""
        return self._result_steps
