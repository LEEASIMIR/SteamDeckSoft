from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, QFileInfo, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QDialogButtonBox, QTabWidget, QWidget, QFileIconProvider,
)

logger = logging.getLogger(__name__)


_icon_provider = QFileIconProvider()


@dataclass
class AppFinderResult:
    exe_path: str
    working_dir: str
    icon_path: str = ""


class _ProcessScanner(QThread):
    finished = pyqtSignal(list)

    def run(self) -> None:
        try:
            import psutil
        except ImportError:
            self.finished.emit([])
            return

        seen: set[str] = set()
        results: list[tuple[str, str]] = []
        windows_dir = os.environ.get("SystemRoot", r"C:\Windows").lower()

        for proc in psutil.process_iter(["name", "exe"]):
            try:
                exe = proc.info["exe"]
                if not exe:
                    continue
                exe_lower = exe.lower()
                if exe_lower.startswith(windows_dir):
                    continue
                if exe_lower in seen:
                    continue
                seen.add(exe_lower)
                name = proc.info["name"] or os.path.basename(exe)
                results.append((name, exe))
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue

        results.sort(key=lambda x: x[0].lower())
        self.finished.emit(results)


class _StartMenuScanner(QThread):
    finished = pyqtSignal(list)

    def run(self) -> None:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                self._scan()
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            logger.exception("Start menu scan failed")
            self.finished.emit([])

    def _scan(self) -> None:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        dirs: list[str] = []

        programdata = os.environ.get("ProgramData", "")
        if programdata:
            dirs.append(os.path.join(programdata, r"Microsoft\Windows\Start Menu\Programs"))

        appdata = os.environ.get("AppData", "")
        if appdata:
            dirs.append(os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"))

        seen: set[str] = set()
        results: list[tuple[str, str]] = []

        for start_dir in dirs:
            if not os.path.isdir(start_dir):
                continue
            for root, _dirs, files in os.walk(start_dir):
                for f in files:
                    if not f.lower().endswith(".lnk"):
                        continue
                    lnk_path = os.path.join(root, f)
                    try:
                        shortcut = shell.CreateShortcut(lnk_path)
                        target = shortcut.TargetPath
                        if not target or not target.lower().endswith(".exe"):
                            continue
                        target_lower = target.lower()
                        if target_lower in seen:
                            continue
                        seen.add(target_lower)
                        name = os.path.splitext(f)[0]
                        results.append((name, target))
                    except Exception:
                        continue

        results.sort(key=lambda x: x[0].lower())
        self.finished.emit(results)


class AppFinderDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find Application")
        self.setMinimumSize(550, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._result: AppFinderResult | None = None
        self._process_scanner: _ProcessScanner | None = None
        self._startmenu_scanner: _StartMenuScanner | None = None

        self._build_ui()
        self._start_scans()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()

        # --- Running Processes tab ---
        proc_tab = QWidget()
        proc_layout = QVBoxLayout(proc_tab)
        self._proc_filter = QLineEdit()
        self._proc_filter.setPlaceholderText("Filter...")
        self._proc_filter.textChanged.connect(lambda t: self._apply_filter(self._proc_list, t))
        proc_layout.addWidget(self._proc_filter)
        self._proc_list = QListWidget()
        self._proc_list.setIconSize(QSize(32, 32))
        self._proc_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._proc_list.currentItemChanged.connect(self._on_selection_changed)
        proc_layout.addWidget(self._proc_list)
        self._proc_loading = QLabel("Loading...")
        self._proc_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        proc_layout.addWidget(self._proc_loading)
        self._tabs.addTab(proc_tab, "Running Processes")

        # --- Start Menu tab ---
        sm_tab = QWidget()
        sm_layout = QVBoxLayout(sm_tab)
        self._sm_filter = QLineEdit()
        self._sm_filter.setPlaceholderText("Filter...")
        self._sm_filter.textChanged.connect(lambda t: self._apply_filter(self._sm_list, t))
        sm_layout.addWidget(self._sm_filter)
        self._sm_list = QListWidget()
        self._sm_list.setIconSize(QSize(32, 32))
        self._sm_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._sm_list.currentItemChanged.connect(self._on_selection_changed)
        sm_layout.addWidget(self._sm_list)
        self._sm_loading = QLabel("Loading...")
        self._sm_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sm_layout.addWidget(self._sm_loading)
        self._tabs.addTab(sm_tab, "Start Menu Programs")

        layout.addWidget(self._tabs)

        # Buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    def _start_scans(self) -> None:
        self._process_scanner = _ProcessScanner()
        self._process_scanner.finished.connect(self._on_processes_loaded)
        self._process_scanner.start()

        self._startmenu_scanner = _StartMenuScanner()
        self._startmenu_scanner.finished.connect(self._on_startmenu_loaded)
        self._startmenu_scanner.start()

    def _populate_list(self, list_widget: QListWidget, items: list[tuple[str, str]], loading_label: QLabel) -> None:
        loading_label.hide()
        if not items:
            loading_label.setText("No applications found")
            loading_label.show()
            return
        for name, exe_path in items:
            item = QListWidgetItem()
            item.setText(f"{name}\n  {exe_path}")
            item.setData(Qt.ItemDataRole.UserRole, exe_path)
            if os.path.isfile(exe_path):
                item.setIcon(_icon_provider.icon(QFileInfo(exe_path)))
            list_widget.addItem(item)

    def _on_processes_loaded(self, results: list[tuple[str, str]]) -> None:
        self._populate_list(self._proc_list, results, self._proc_loading)

    def _on_startmenu_loaded(self, results: list[tuple[str, str]]) -> None:
        self._populate_list(self._sm_list, results, self._sm_loading)

    def _apply_filter(self, list_widget: QListWidget, text: str) -> None:
        text_lower = text.lower()
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item is not None:
                item.setHidden(text_lower not in item.text().lower())

    def _current_list(self) -> QListWidget:
        if self._tabs.currentIndex() == 0:
            return self._proc_list
        return self._sm_list

    def _on_selection_changed(self) -> None:
        current = self._current_list().currentItem()
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
            current is not None and not current.isHidden()
        )

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self._on_accept()

    def _on_accept(self) -> None:
        current = self._current_list().currentItem()
        if current is None:
            return
        exe_path = current.data(Qt.ItemDataRole.UserRole)
        if exe_path:
            working_dir = os.path.dirname(exe_path)
            icon_path = self._save_icon(exe_path)
            self._result = AppFinderResult(
                exe_path=exe_path, working_dir=working_dir, icon_path=icon_path,
            )
            self.accept()

    def _save_icon(self, exe_path: str) -> str:
        """Extract the exe icon and save as PNG. Returns saved path or empty."""
        try:
            import hashlib

            icons_dir = os.path.join(
                os.environ.get("APPDATA", ""), "SoftDeck", "icons",
            )
            os.makedirs(icons_dir, exist_ok=True)

            basename = os.path.splitext(os.path.basename(exe_path))[0].lower()
            path_hash = hashlib.md5(exe_path.lower().encode()).hexdigest()[:8]
            icon_file = os.path.join(icons_dir, f"{basename}_{path_hash}.png")

            if os.path.isfile(icon_file):
                return icon_file

            icon = _icon_provider.icon(QFileInfo(exe_path))
            sizes = icon.availableSizes()
            if sizes:
                best = max(sizes, key=lambda s: s.width() * s.height())
            else:
                best = QSize(32, 32)

            pixmap = icon.pixmap(best)
            if not pixmap.isNull() and pixmap.save(icon_file, "PNG"):
                return icon_file
        except Exception:
            logger.debug("Failed to save icon for %s", exe_path, exc_info=True)
        return ""

    def get_result(self) -> AppFinderResult | None:
        return self._result
