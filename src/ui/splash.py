from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import QSplashScreen, QApplication


class Splash(QSplashScreen):
    """Minimal startup splash — auto-closes after a short delay."""

    _WIDTH = 320
    _HEIGHT = 160
    _DURATION_MS = 1800

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self._WIDTH) // 2
            y = geo.y() + (geo.height() - self._HEIGHT) // 2
            self.move(x, y)

    def show_and_close(self) -> None:
        self.show()
        QTimer.singleShot(self._DURATION_MS, self._fade_close)

    def _fade_close(self) -> None:
        self.close()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background rounded rect
        bg = QColor("#0a0a0a")
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self._WIDTH, self._HEIGHT, 16, 16)

        # Accent line at top
        grad = QLinearGradient(0, 0, self._WIDTH, 0)
        grad.setColorAt(0.0, QColor("#e94560"))
        grad.setColorAt(1.0, QColor("#533483"))
        p.setBrush(grad)
        p.drawRoundedRect(0, 0, self._WIDTH, 4, 2, 2)

        # App name
        font_title = QFont("Segoe UI", 20)
        font_title.setBold(True)
        p.setFont(font_title)
        p.setPen(QColor("#e94560"))
        p.drawText(self.rect().adjusted(0, 30, 0, -40), Qt.AlignmentFlag.AlignCenter, "SteamDeckSoft")

        # Subtitle
        font_sub = QFont("Segoe UI", 10)
        p.setFont(font_sub)
        p.setPen(QColor("#808080"))
        p.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter, "Loading...")

        # Border
        p.setPen(QColor("#1a1a1a"))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, self._WIDTH, self._HEIGHT, 16, 16)

        p.end()
