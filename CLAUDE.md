# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SteamDeckSoft is a Windows-only PyQt6 desktop app that acts as a configurable button deck (similar to Stream Deck). It presents a grid of customizable buttons that can launch apps, send hotkeys, input text macros, control media, monitor system stats, open URLs, and navigate between folders. Buttons are organized in an infinitely nestable folder tree structure, navigated via a toggleable left-side tree panel. It runs as a single-instance frameless always-on-top resizable window with a system tray icon, adjustable opacity, and supports a global hotkey to toggle visibility.

## Running

```bash
python main.py
```

Dependencies: `pip install -r requirements.txt` (requires Windows — uses pywin32, pycaw, comtypes, keyboard).

## Architecture

**Entry flow:** `main.py` checks single-instance via Win32 Named Mutex (`CreateMutexW`) **before any imports**, then → `src/app.py:SteamDeckSoftApp` (subclasses QApplication). This prevents a second instance from importing `keyboard` or creating a QApplication, which could interfere with the first instance's Win32 keyboard hooks.

**Initialization order in `SteamDeckSoftApp.__init__`:**
1. Logging setup
2. Splash screen shown (auto-closes after 1.8s)
3. `ConfigManager` load
4. `ActionRegistry` + action registration
5. `InputDetector` start
6. `MainWindow` construction
7. `TrayIcon` construction
8. Background services start (`SystemStatsService`, optionally `ActiveWindowMonitor`)
9. `GlobalHotkeyService` start
10. Dark theme applied, window shown only if Num Lock is OFF (Num Lock ON → start hidden)

**Five main subsystems:**

1. **Config** (`src/config/`) — Dataclass-based models (`AppConfig` v2 → `AppSettings` + `FolderConfig` (recursive tree) → `ButtonConfig[]` → `ActionConfig`). `FolderConfig` supports infinite nesting via `children: list[FolderConfig]`. `ButtonConfig` includes per-button styling: `label_color` (hex string, default empty = white), `label_size` (int px, default 0 = use `AppSettings.default_label_size`). `ConfigManager` handles load/save with atomic writes (tmp file + `shutil.move`), plus `export_config(path)`/`import_config(path)` for JSON file export/import. User config lives at `%APPDATA%/SteamDeckSoft/config.json`, falling back to `config/default_config.json`. Automatic v1→v2 migration converts flat `pages` list to `root_folder` tree. `AppSettings` includes `default_label_size` (int px, default 15, range 8–48 in Settings UI), `global_hotkey` (default `"ctrl+\`"`), `window_opacity` (0.2–1.0, default 1.0), `folder_tree_visible` (default `True`), `window_x`/`window_y` (last window position, `None` = center-top of primary screen).

2. **Actions** (`src/actions/`) — Plugin-like system. `ActionBase` is the ABC with `execute(params)` and `get_display_text(params)`. `ActionRegistry` maps string type names to action instances and holds an optional `main_window` reference for `NavigateFolderAction`. Current types: `launch_app`, `hotkey`, `text_input`, `media_control`, `system_monitor`, `navigate_folder` (+ `navigate_page` alias for backward compat), `open_url`, `macro`. `LaunchAppAction` uses `os.startfile()` as primary method (handles GUI/console apps, documents, URLs) with `subprocess.Popen(CREATE_NEW_CONSOLE)` fallback when arguments are provided. `HotkeyAction` has `_SPECIAL_HOTKEYS` dict for Windows-protected shortcuts (e.g., `win+l` → `LockWorkStation()` API). `OpenUrlAction` uses `webbrowser.open()`. To add a new action: subclass `ActionBase`, register it in `SteamDeckSoftApp._register_actions()`.

3. **Services** (`src/services/`) — Background workers:
   - `SystemStatsService(QThread)` — polls CPU/RAM via psutil, emits `stats_updated(float, float)`
   - `ActiveWindowMonitor(QThread)` — polls foreground window via win32gui/win32process, emits `active_app_changed(str)` to drive auto-folder-switching
   - `MediaControlService` — wraps pycaw `AudioDevice.EndpointVolume` for volume control (not a QThread, plain helper; pycaw ≥20251023 uses `.EndpointVolume` property instead of legacy `.Activate()` COM call)
   - `GlobalHotkeyService(QObject)` — registers system-wide hotkey via `keyboard` library, emits `triggered` signal connected to `MainWindow.toggle_visibility`. Supports live rebinding via `update_hotkey()`. Has periodic hook refresh (`QTimer`, 5s interval) that re-registers the hotkey to recover from silent hook removal by Windows.
   - `InputDetector` — plain Python class using `ctypes` Win32 `WH_KEYBOARD_LL` hook in a daemon thread to detect injected (software-generated) keystrokes. Exposes `last_was_injected: bool`, used by `MainWindow.keyPressEvent` to prevent recursive triggering from `keyboard.send()`. Also detects Num Lock toggles and emits `numpad_signal.numlock_changed(bool)` to drive window visibility (Num Lock ON → hide, OFF → show). Numpad 0 (VK_INSERT when Num Lock OFF) emits `numpad_signal.back_pressed` → `MainWindow.navigate_back()` to go to parent folder. Static method `is_numlock_on()` checks current state at startup. Has `_passthrough` flag toggled via `set_passthrough(bool)` — when True, numpad keys pass through to the active window instead of being intercepted (used when dialogs are open so numpad can type numbers). **Hook reliability:** Uses `SetTimer` (5s interval) to periodically reinstall the `WH_KEYBOARD_LL` hook via `_reinstall_hook()`, guarding against Windows silently removing the hook when the Python GIL delays the callback beyond `LowLevelHooksTimeout` (~300ms) — particularly common on multi-monitor setups with different DPI scaling. **Num Lock polling fallback:** A separate fast `SetTimer` (50ms) polls `GetKeyState(VK_NUMLOCK)` via `_poll_numlock()` to catch missed Num Lock events when the hook is silently removed. `_last_numlock_state` tracks the last known state to prevent duplicate emissions between hook and polling.

4. **UI** (`src/ui/`) — Frameless `MainWindow` with custom `TitleBar` (defined in `main_window.py`, provides drag support + folder tree toggle button + opacity slider + tray button + right-click context menu with Settings / Export Config / Import Config). TitleBar height is 55px with top-aligned layout. Window supports 8-direction edge drag resize (`_Edge` IntFlag + `_EDGE_CURSORS` mapping, 6px margin detection). Layout: `QVBoxLayout(TitleBar + QSplitter(FolderTreeWidget | GridContainer))`. `FolderTreeWidget` (in `folder_tree.py`) is a `QTreeWidget` showing the recursive folder structure with drag-and-drop reordering and right-click context menu (New Sub-Folder / Rename / Edit / Delete). `QGridLayout` of `DeckButton` widgets with unified black background (`#0a0a0a`). `DeckButton` overrides `paintEvent` when an icon is set: draws button background → icon (full opacity, centered) → label text on top, applying per-button `label_color` and `label_size`. Font size priority: per-button `label_size` > 0 → use that value; otherwise → `AppSettings.default_label_size`. Buttons are right-click editable via `ButtonEditorDialog` (uses `QStackedWidget` per action type; includes `HotkeyRecorderWidget` for keyboard capture with `grabKeyboard()`, color picker for label color, font size spin box); button context menu also supports Copy/Paste to duplicate button configs across positions. All dialog `.exec()` calls are wrapped with `set_numpad_passthrough(True/False)` to allow numpad input while editing. Folders managed via `FolderEditorDialog`. Settings via `SettingsDialog` (button size/spacing/default font size, behavior, appearance — grid rows/cols hidden from UI). `TrayIcon` provides show/settings/reset position/quit context menu and double-click to show.

5. **Styles** (`src/ui/styles.py`) — Pure black/charcoal theme: background `#0e0e0e`, buttons `#0a0a0a`, title bar `#080808`, borders `#1a1a1a`–`#2a2a2a`, accent `#e94560`. Exports `DARK_THEME`, `DECK_BUTTON_STYLE` (static black, base font-size 15px), `DECK_BUTTON_EMPTY_STYLE`, `MONITOR_BUTTON_STYLE`, `FOLDER_TREE_STYLE`, `TITLE_BAR_STYLE`.

**Key data flow:** Config defines a root folder tree → each folder has `buttons` and `children` (sub-folders) → the grid shows the current folder's buttons → each button has an `ActionConfig(type, params)` → on click, `ActionRegistry.execute(type, params)` dispatches to the matching `ActionBase` subclass → services feed live data back to the UI via Qt signals. The folder tree panel allows navigation between folders; clicking a folder loads its buttons into the grid. Buttons can be copied/pasted via `DeckButton._clipboard` (class-level dict storing `ButtonConfig.to_dict()` data).

**Keyboard shortcuts:** Global numpad keys (Num Lock OFF, via `InputDetector` hook) map numpad-layout keys (7-8-9/4-5-6/1-2-3) to grid positions `(row, col)` in the top-left 3x3 area. Numpad 0 navigates back to the parent folder (no-op at root).

**Window behavior:** `closeEvent` minimizes to tray instead of quitting. `toggle_visibility` hides to tray or `show_on_primary()` (restores to last saved position, or centers on primary screen top edge if none saved). Window position is persisted to `AppSettings.window_x`/`window_y` on every move via `moveEvent`. `reset_position()` clears saved position and centers on primary screen (accessible via tray menu "Reset Position"). Window uses `setMinimumSize` (not `setFixedSize`) to allow drag resize. `set_opacity(value)` applies opacity and persists to config. TitleBar has a horizontal `QSlider` (20–100%) for real-time opacity control. **Num Lock–driven visibility:** Num Lock ON hides the window, Num Lock OFF shows it. This is checked both at startup and on every Num Lock toggle via `InputDetector`.

## Conventions

- All modules use `from __future__ import annotations` and `TYPE_CHECKING` guards for type-only imports
- Private attributes prefixed with `_`; no public setters except through property accessors
- Qt signals/slots for all cross-component communication
- Button positions are `(row, col)` tuples
- Config uses `to_dict()`/`from_dict()` pattern (no Pydantic)
- Dialogs use lazy imports to avoid circular dependencies
- Services are injected via setter methods (e.g., `set_main_window()`, `set_media_service()`, `set_input_detector()`)
- New folder IDs use `uuid.uuid4().hex[:8]`
- Config version is 2; v1 configs are auto-migrated on load

## File Map

```
main.py                          # Entry point — Win32 Named Mutex single-instance check before any imports
src/app.py                       # SteamDeckSoftApp — orchestrates everything
src/config/models.py             # Dataclasses: AppConfig, AppSettings, FolderConfig, ButtonConfig, ActionConfig (+ deprecated PageConfig for migration)
src/config/manager.py            # ConfigManager — load/save with atomic writes + folder CRUD + export/import
src/actions/base.py              # ActionBase ABC
src/actions/registry.py          # ActionRegistry — type→action dispatch + main_window ref
src/actions/launch_app.py        # LaunchAppAction — os.startfile primary / subprocess.Popen(CREATE_NEW_CONSOLE) with args
src/actions/hotkey.py            # HotkeyAction — keyboard.send() + _SPECIAL_HOTKEYS (win+l → LockWorkStation)
src/actions/text_input.py        # TextInputAction — keyboard.write() or clipboard paste (win32clipboard + Ctrl+V)
src/actions/media.py             # MediaControlAction — volume via pycaw, media keys via keyboard
src/actions/navigate.py          # NavigateFolderAction — folder switching via registry.main_window
src/actions/system_monitor.py    # SystemMonitorAction — display-only, live data via DeckButton
src/actions/open_url.py          # OpenUrlAction — webbrowser.open()
src/services/system_stats.py     # SystemStatsService(QThread) — CPU/RAM polling
src/services/window_monitor.py   # ActiveWindowMonitor(QThread) — foreground window tracking
src/services/media_control.py    # MediaControlService — pycaw IAudioEndpointVolume wrapper
src/services/global_hotkey.py    # GlobalHotkeyService(QObject) — system-wide hotkey + periodic hook refresh (QTimer 5s)
src/services/input_detector.py   # InputDetector — Win32 keyboard hook + periodic reinstall (SetTimer 5s) + Num Lock state polling fallback (50ms)
src/ui/main_window.py           # MainWindow + TitleBar — frameless resizable window, QSplitter(tree|grid), opacity slider, position persistence
src/ui/button_widget.py         # DeckButton(QPushButton) — black buttons, custom paintEvent (icon behind text), context menu (edit/clear/copy/paste)
src/ui/folder_tree.py           # FolderTreeWidget(QTreeWidget) — left panel folder tree with drag-and-drop
src/ui/folder_editor_dialog.py  # FolderEditorDialog — name + mapped apps list for folders
src/ui/button_editor_dialog.py  # ButtonEditorDialog — per-action-type stacked editor + HotkeyRecorderWidget
src/ui/settings_dialog.py       # SettingsDialog — grid/behavior/appearance settings
src/ui/splash.py                # Splash — startup splash screen (auto-close, 320x160, black + accent gradient)
src/ui/styles.py                # All style constants
src/ui/tray_icon.py             # TrayIcon(QSystemTrayIcon) — system tray with context menu (show/settings/reset position/quit)
build.bat                        # PyInstaller build script → dist/SteamDeckSoft.exe
config/default_config.json       # Default 3x3 grid: Root(media+monitor) → Apps(system utils) → Shortcuts(hotkeys) (v2 format)
USAGE.md                         # User manual — reference (Korean)
GUIDE.md                         # User manual — beginner-friendly guide (Korean)
docs/SteamDeckSoft_Guide.pdf     # PDF version of GUIDE.md (generated by docs/build_pdf.py)
docs/build_pdf.py                # Script to regenerate the PDF guide
```
