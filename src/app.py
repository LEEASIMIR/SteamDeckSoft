from __future__ import annotations

import ctypes
import logging
import os
from pathlib import Path
import sys
import time

import psutil

# Prevent the keyboard library from ever installing a WH_KEYBOARD_LL hook.
# Its hook interferes with our numpad_hook.exe even in a separate process.
import keyboard as _kb
_kb._listener.start_if_necessary = lambda: None

from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from .config.manager import ConfigManager
from .actions.registry import ActionRegistry
from .actions.launch_app import LaunchAppAction
from .actions.hotkey import HotkeyAction
from .actions.system_monitor import SystemMonitorAction
from .actions.navigate import NavigateBackAction, NavigateFolderAction, NavigateParentAction
from .actions.text_input import TextInputAction
from .actions.macro import MacroAction
from .actions.open_url import OpenUrlAction
from .actions.open_folder import OpenFolderAction
from .actions.run_command import RunCommandAction
from .services.system_stats import SystemStatsService
from .services.window_monitor import ActiveWindowMonitor

from .services.input_detector import InputDetector
from .ui.main_window import MainWindow
from .ui.tray_icon import TrayIcon
from .ui.styles import get_theme
from .ui.toast import ToastManager
from .plugins.loader import PluginLoader

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

logger = logging.getLogger(__name__)

_MUTEX_NAME = "SoftDeck_SingleInstance"


class SoftDeckApp(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("SoftDeck")
        self.setQuitOnLastWindowClosed(False)

        self._instance_mutex = None
        self._setup_logging()

        # Single instance: kill existing process if running
        self._ensure_single_instance()

        # Splash screen
        self._splash = self._create_splash()
        self._splash.show()
        self._splash_shown_at = time.monotonic()
        self.processEvents()

        # Config
        self._config_manager = ConfigManager()
        self._config_manager.load()

        # Resolve theme
        self._theme = get_theme(self._config_manager.settings.theme)

        # Toast notifications
        self._toast_manager = ToastManager(self._theme.palette)

        # Actions
        self._action_registry = ActionRegistry()
        self._register_actions()

        # Plugins
        self._plugin_loader = PluginLoader()
        self._load_plugins()

        # Input detector (injected key filter + global numpad shortcuts)
        self._input_detector = InputDetector()
        if self._config_manager.settings.input_mode == "shortcut":
            self._input_detector.start()

        # Main window
        self._main_window = MainWindow(self._config_manager, self._action_registry, self._plugin_loader)
        self._main_window.set_input_detector(self._input_detector)
        self._input_detector.numpad_signal.pressed.connect(self._main_window.on_global_numpad)
        self._input_detector.numpad_signal.numlock_changed.connect(self._on_numlock_changed)
        self._action_registry.set_main_window(self._main_window)
        self._main_window.set_toast_manager(self._toast_manager)

        # Tray
        self._tray_icon = TrayIcon(self._main_window)
        self._tray_icon.show()

        # Services
        self._start_services()

        # Apply theme
        self.setStyleSheet(self._theme.dark_theme)

        # Determine if main window should show at startup
        self._should_show_window = (
            self._config_manager.settings.input_mode == "widget"
            or not self._input_detector.is_numlock_on()
        )
        if not self._should_show_window:
            logger.info("Num Lock is ON at startup — window hidden")

        # Ready feedback (deferred — splash transition then show window)
        self._transition_group = None
        self._notify_ready()

    def _setup_logging(self) -> None:
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        handlers: list[logging.Handler] = []

        # File log — always works, even in --windowed exe (no stdout)
        log_dir = os.path.join(
            os.environ.get("APPDATA", "."), "SoftDeck"
        )
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "app.log"), encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

        # Console log — only when stdout exists (not --windowed exe)
        if sys.stdout is not None:
            handlers.append(logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers,
        )

    def _register_actions(self) -> None:
        self._action_registry.register("launch_app", LaunchAppAction())
        self._action_registry.register("hotkey", HotkeyAction())
        self._action_registry.register("text_input", TextInputAction())
        self._action_registry.register("macro", MacroAction())
        self._action_registry.register("system_monitor", SystemMonitorAction())
        self._action_registry.register("open_url", OpenUrlAction())
        self._action_registry.register("open_folder", OpenFolderAction())
        self._action_registry.register("run_command", RunCommandAction())

        nav_action = NavigateFolderAction(self._action_registry)
        self._action_registry.register("navigate_folder", nav_action)
        # Backward compat: old configs with navigate_page type
        self._action_registry.register("navigate_page", nav_action)

        nav_parent = NavigateParentAction(self._action_registry)
        self._action_registry.register("navigate_parent", nav_parent)

        nav_back = NavigateBackAction(self._action_registry)
        self._action_registry.register("navigate_back", nav_back)

    def _load_plugins(self) -> None:
        self._plugin_loader.discover_and_load()
        for action_type, plugin in self._plugin_loader.plugins.items():
            self._action_registry.register(action_type, plugin.create_action())
        from .ui.default_icons import set_plugin_icon_resolver
        set_plugin_icon_resolver(self._plugin_loader.get_icon_path)

    def _start_services(self) -> None:
        # System stats
        self._stats_service = SystemStatsService(interval_ms=2000)
        self._stats_service.stats_updated.connect(self._main_window.update_monitor_button)
        self._main_window.set_system_stats_service(self._stats_service)
        self._stats_service.start()

        # Window monitor
        if self._config_manager.settings.auto_switch_enabled:
            self._window_monitor = ActiveWindowMonitor(interval_ms=300)
            self._window_monitor.active_app_changed.connect(self._on_active_app_changed)
            self._main_window.set_window_monitor(self._window_monitor)
            self._window_monitor.start()
        else:
            self._window_monitor = None

        # Media playback monitor
        self._playback_monitor = None
        self._mute_timer = None
        self._mic_mute_timer = None
        self._device_name_timer = None
        media_plugin = self._plugin_loader.plugins.get("media_control")
        if media_plugin is not None:
            monitor = media_plugin.get_playback_monitor()
            if monitor is not None and monitor.available:
                monitor.playback_state_changed.connect(self._on_media_state_changed)
                monitor.track_info_changed.connect(self._on_track_info_changed)
                monitor.start()
                self._playback_monitor = monitor
                logger.info("Media playback monitor started")
            # Mute state polling (main-thread QTimer to avoid COM threading issues)
            service = media_plugin.get_service()
            if service is not None:
                self._last_mute_state = service.is_muted()
                self._mute_service = service
                self._mute_timer = QTimer()
                self._mute_timer.timeout.connect(self._poll_mute_state)
                self._mute_timer.start(500)
                logger.info("Mute state polling started")

                # Mic mute state polling
                self._last_mic_mute_state = service.is_mic_muted()
                self._mic_mute_timer = QTimer()
                self._mic_mute_timer.timeout.connect(self._poll_mic_mute_state)
                self._mic_mute_timer.start(500)
                logger.info("Mic mute state polling started")

                # Audio device name polling
                self._last_device_name = service.get_current_audio_output_name()
                self._main_window.update_device_name(self._last_device_name)
                self._device_name_timer = QTimer()
                self._device_name_timer.timeout.connect(self._poll_device_name)
                self._device_name_timer.start(2000)
                logger.info("Audio device name polling started")

    def _on_numlock_changed(self, is_on: bool) -> None:
        """Hide window when Num Lock is ON, show when OFF."""
        if self._config_manager.settings.input_mode == "widget":
            return
        if is_on:
            self._main_window.hide()
        else:
            # Re-check actual Num Lock state before showing
            if self._input_detector.is_numlock_on():
                return
            self._main_window.show_on_primary()
            self._sync_folder_to_foreground()

    def _sync_folder_to_foreground(self) -> None:
        """Switch to the mapped folder for the current foreground app."""
        if not self._config_manager.settings.auto_switch_enabled:
            return
        if self._window_monitor is None:
            return
        try:
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid or pid == os.getpid():
                return
            proc = psutil.Process(pid)
            exe_name = proc.name()
            folder = self._config_manager.find_folder_for_app(exe_name)
            if folder is not None:
                self._main_window.switch_to_folder_id(folder.id)
            # Keep the monitor in sync to avoid duplicate signal
            self._window_monitor._last_exe = exe_name
        except Exception:
            logger.debug("Failed to sync folder to foreground", exc_info=True)

    def _on_active_app_changed(self, exe_name: str) -> None:
        if not self._config_manager.settings.auto_switch_enabled:
            return
        folder = self._config_manager.find_folder_for_app(exe_name)
        if folder is not None:
            self._main_window.switch_to_folder_id(folder.id)

    def _on_media_state_changed(self, is_playing: bool) -> None:
        media_plugin = self._plugin_loader.plugins.get("media_control")
        if media_plugin is not None:
            media_plugin._is_playing = is_playing
        self._main_window.update_media_state(is_playing)

    def _poll_mute_state(self) -> None:
        try:
            muted = self._mute_service.is_muted()
        except Exception:
            return
        if muted != self._last_mute_state:
            self._last_mute_state = muted
            media_plugin = self._plugin_loader.plugins.get("media_control")
            if media_plugin is not None:
                media_plugin._is_muted = muted
            self._main_window.update_mute_state(muted)

    def _poll_mic_mute_state(self) -> None:
        try:
            muted = self._mute_service.is_mic_muted()
        except Exception:
            return
        if muted != self._last_mic_mute_state:
            self._last_mic_mute_state = muted
            media_plugin = self._plugin_loader.plugins.get("media_control")
            if media_plugin is not None:
                media_plugin._is_mic_muted = muted
            self._main_window.update_mic_mute_state(muted)

    def _on_track_info_changed(self, text: str, thumbnail: bytes = b"") -> None:
        self._main_window.update_now_playing(text, thumbnail)

    def _poll_device_name(self) -> None:
        try:
            name = self._mute_service.get_current_audio_output_name()
        except Exception:
            return
        if name != self._last_device_name:
            self._last_device_name = name
            self._main_window.update_device_name(name)

    def _notify_ready(self) -> None:
        """Wait for minimum splash time, then start transition animation."""
        remaining_ms = 0
        if self._splash is not None:
            _SPLASH_MIN_SECONDS = 3.0
            elapsed = time.monotonic() - self._splash_shown_at
            remaining_ms = max(0, int((_SPLASH_MIN_SECONDS - elapsed) * 1000))
        QTimer.singleShot(remaining_ms, self._begin_transition)

    def _begin_transition(self) -> None:
        """Splash slides to main window position + cross-fade into the app."""
        # No splash or window shouldn't show → skip animation
        if self._splash is None or not self._should_show_window:
            if self._splash is not None:
                self._splash.close()
                self._splash = None
            if self._should_show_window:
                self._main_window.show_on_primary()
            self._on_ready()
            return

        # Compute main window target position
        settings = self._config_manager.settings
        target_opacity = settings.window_opacity
        if settings.window_x is not None and settings.window_y is not None:
            target_pos = QPoint(settings.window_x, settings.window_y)
        else:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            geo = screen.availableGeometry()
            margin = 12
            target_pos = QPoint(
                geo.x() + geo.width() - self._main_window.width() - margin,
                geo.y() + geo.height() - self._main_window.height() - margin,
            )

        # Show main window transparent at target position
        self._main_window.setWindowOpacity(0.0)
        self._main_window.move(target_pos)
        self._main_window.show()

        # Splash destination: centered over the main window
        win_center_x = target_pos.x() + self._main_window.width() // 2
        win_center_y = target_pos.y() + self._main_window.height() // 2
        splash_end = QPoint(
            win_center_x - self._splash.width() // 2,
            win_center_y - self._splash.height() // 2,
        )

        duration = 800

        # Splash — slide to main window center
        splash_move = QPropertyAnimation(self._splash, b"pos")
        splash_move.setDuration(duration)
        splash_move.setStartValue(self._splash.pos())
        splash_move.setEndValue(splash_end)
        splash_move.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Splash — fade out
        splash_fade = QPropertyAnimation(self._splash, b"windowOpacity")
        splash_fade.setDuration(duration)
        splash_fade.setStartValue(1.0)
        splash_fade.setEndValue(0.0)
        splash_fade.setEasingCurve(QEasingCurve.Type.InCubic)

        # Main window — fade in
        win_fade = QPropertyAnimation(self._main_window, b"windowOpacity")
        win_fade.setDuration(duration)
        win_fade.setStartValue(0.0)
        win_fade.setEndValue(target_opacity)
        win_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Run all in parallel
        self._transition_group = QParallelAnimationGroup()
        self._transition_group.addAnimation(splash_move)
        self._transition_group.addAnimation(splash_fade)
        self._transition_group.addAnimation(win_fade)
        self._transition_group.finished.connect(self._on_transition_finished)
        self._transition_group.start()

    def _on_transition_finished(self) -> None:
        if self._splash is not None:
            self._splash.close()
            self._splash = None
        self._transition_group = None
        self._on_ready()

    def _on_ready(self) -> None:
        import winsound
        self._toast_manager.show("SoftDeck", "Ready", duration_ms=2000)
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)

    # ------------------------------------------------------------------
    # Splash screen
    # ------------------------------------------------------------------

    def _create_splash(self) -> QSplashScreen:
        from .version import APP_VERSION

        size = 280
        icon_size = 128
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient
        grad = QLinearGradient(0, 0, 0, size)
        grad.setColorAt(0.0, QColor("#1a1a2e"))
        grad.setColorAt(1.0, QColor("#16213e"))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, size, size, 20, 20)

        # Icon
        icon_path = _ASSETS_DIR / "트레이아이콘후보1.png"
        if icon_path.exists():
            icon_pm = QPixmap(str(icon_path)).scaled(
                icon_size, icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (size - icon_pm.width()) // 2
            y = 40
            painter.drawPixmap(x, y, icon_pm)

        # Title
        font = painter.font()
        font.setPixelSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#e0e0e0"))
        painter.drawText(0, 185, size, 30, Qt.AlignmentFlag.AlignCenter, "SoftDeck")

        # Version
        font.setPixelSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#888888"))
        painter.drawText(0, 210, size, 20, Qt.AlignmentFlag.AlignCenter, f"v{APP_VERSION}")

        # Loading
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        painter.drawText(0, 245, size, 20, Qt.AlignmentFlag.AlignCenter, "Loading...")

        painter.end()

        splash = QSplashScreen(pixmap)
        splash.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint,
        )
        splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        return splash

    # ------------------------------------------------------------------
    # Single-instance helpers
    # ------------------------------------------------------------------

    def _acquire_mutex(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(handle)
            return False
        self._instance_mutex = handle
        return True

    def _kill_existing(self) -> None:
        my_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.pid == my_pid:
                    continue
                name = proc.info["name"] or ""
                if name.lower() == "softdeck.exe":
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info("Terminated existing PID %d", proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    logger.info("Force-killed existing PID %d", proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def _ensure_single_instance(self) -> None:
        if self._acquire_mutex():
            return

        logger.info("Another instance detected — terminating it")
        self._kill_existing()

        for _ in range(20):
            time.sleep(0.25)
            self.processEvents()
            if self._acquire_mutex():
                logger.info("Mutex acquired after killing existing process")
                return

        logger.error("Failed to acquire mutex after killing existing process")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Input mode switching
    # ------------------------------------------------------------------

    def apply_input_mode(self) -> None:
        """Switch between shortcut and widget mode live (no restart)."""
        mode = self._config_manager.settings.input_mode
        if mode == "widget":
            if self._input_detector.is_running:
                self._input_detector.stop()
                logger.info("Switched to widget mode — InputDetector stopped")
            self._main_window.show_on_primary()
        else:  # shortcut
            if not self._input_detector.is_running:
                self._input_detector.start()
                logger.info("Switched to shortcut mode — InputDetector started")
            if self._input_detector.is_numlock_on():
                self._main_window.hide()
            else:
                self._main_window.show_on_primary()

    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        logger.info("Shutting down...")
        if hasattr(self, "_tray_icon"):
            self._tray_icon.hide()
        if hasattr(self, "_input_detector"):
            self._input_detector.stop()
        if hasattr(self, "_stats_service"):
            self._stats_service.stop()
        if hasattr(self, "_window_monitor") and self._window_monitor is not None:
            self._window_monitor.stop()
        if hasattr(self, "_playback_monitor") and self._playback_monitor is not None:
            self._playback_monitor.stop()
        if hasattr(self, "_plugin_loader"):
            self._plugin_loader.shutdown_all()
        if self._instance_mutex:
            ctypes.windll.kernel32.CloseHandle(self._instance_mutex)
            self._instance_mutex = None
