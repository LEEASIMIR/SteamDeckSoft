from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import uuid
from pathlib import Path

from src.version import APP_VERSION

from .models import AppConfig, FolderConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "default_config.json"
_USER_CONFIG_DIR = Path(os.environ.get("APPDATA", "~")) / "SoftDeck"
_USER_CONFIG_PATH = _USER_CONFIG_DIR / "config.json"
_ICONS_DIR = _USER_CONFIG_DIR / "icons"

# ActionConfig.params keys that may contain icon file paths
_ICON_PARAM_KEYS = frozenset({
    "play_icon", "pause_icon", "mute_icon", "unmute_icon",
    "mic_on_icon", "mic_off_icon",
})


class ConfigManager:
    def __init__(self) -> None:
        self._config: AppConfig = AppConfig()
        self._path = _USER_CONFIG_PATH

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def settings(self):
        return self._config.settings

    @property
    def root_folder(self) -> FolderConfig:
        return self._config.root_folder

    def load(self) -> AppConfig:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                old_version = data.get("version", 1)
                old_app_version = data.get("app_version", "")
                self._config = AppConfig.from_dict(data)
                logger.info("Loaded user config from %s", self._path)
                needs_save = False
                if old_version < 2:
                    logger.info("Migrated config from v%d to v2", old_version)
                    needs_save = True
                if old_app_version != APP_VERSION:
                    logger.info("App version updated: %s -> %s", old_app_version or "(none)", APP_VERSION)
                    needs_save = True
                # Migrate grid_rows 3 → 4 (added numpad 0/. row)
                if self._config.settings.grid_rows < 4:
                    self._config.settings.grid_rows = 4
                    logger.info("Migrated grid_rows to 4 (numpad 0/. row)")
                    needs_save = True
                if self._inject_example_folders(old_app_version):
                    needs_save = True
                if needs_save:
                    self.save()
                return self._config
            except Exception:
                logger.exception("Failed to load user config, falling back to default")

        if _DEFAULT_CONFIG_PATH.exists():
            try:
                data = json.loads(_DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
                self._config = AppConfig.from_dict(data)
                logger.info("Loaded default config")
            except Exception:
                logger.exception("Failed to load default config, using built-in defaults")
                self._config = AppConfig()
        else:
            self._config = AppConfig()

        self._inject_example_folders("")
        self.save()
        return self._config

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = self._path.with_suffix(".tmp")
        try:
            tmp_path.write_text(
                json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            shutil.move(str(tmp_path), str(self._path))
            logger.info("Config saved to %s", self._path)
        except Exception:
            logger.exception("Failed to save config")
            if tmp_path.exists():
                tmp_path.unlink()

    # --- Example folder injection ---

    @staticmethod
    def _version_tuple(v: str) -> tuple:
        """Parse version for comparison. '' < '0.1.0-beta' < '0.1.0' < '0.1.1'."""
        if not v:
            return ((), 0)
        base, _, pre = v.partition("-")
        nums = tuple(int(x) for x in base.split(".") if x.isdigit())
        return (nums, 0 if pre else 1)

    def _inject_example_folders(self, old_app_version: str = "") -> bool:
        """Inject example folders from config/examples/*.json into root_folder.

        Injects when old_app_version is empty or lower than the example's version.
        Skips folders whose generated name already exists in root_folder.children.
        Returns True if any folders were added.
        """
        examples_dir = _DEFAULT_CONFIG_PATH.parent / "examples"
        if not examples_dir.is_dir():
            return False

        old_ver = self._version_tuple(old_app_version)
        existing_names = {c.name for c in self._config.root_folder.children}
        added = False

        for json_file in sorted(examples_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Failed to read example file: %s", json_file)
                continue

            file_version = data.get("version", "")
            if not file_version:
                continue
            if self._version_tuple(file_version) <= old_ver:
                continue

            name_suffix = data.get("name_suffix", "")
            if not name_suffix:
                continue

            folder_name = f"{file_version}_{name_suffix}"
            if folder_name in existing_names:
                continue

            folder_dict = data.get("folder")
            if not folder_dict or not isinstance(folder_dict, dict):
                continue

            folder_dict["name"] = folder_name
            self._regenerate_folder_ids(folder_dict)
            new_folder = FolderConfig.from_dict(folder_dict)
            self._config.root_folder.children.append(new_folder)
            existing_names.add(folder_name)
            added = True
            logger.info("Injected example folder '%s' from %s", folder_name, json_file.name)

        return added

    # --- Folder operations ---

    def get_folder_by_id(self, folder_id: str) -> FolderConfig | None:
        """DFS search for a folder by id."""
        return self._find_folder(self._config.root_folder, folder_id)

    def _find_folder(self, folder: FolderConfig, folder_id: str) -> FolderConfig | None:
        if folder.id == folder_id:
            return folder
        for child in folder.children:
            result = self._find_folder(child, folder_id)
            if result is not None:
                return result
        return None

    def find_parent_folder(self, folder_id: str) -> FolderConfig | None:
        """Find the parent of a folder by id."""
        return self._find_parent(self._config.root_folder, folder_id)

    def _find_parent(self, folder: FolderConfig, folder_id: str) -> FolderConfig | None:
        for child in folder.children:
            if child.id == folder_id:
                return folder
            result = self._find_parent(child, folder_id)
            if result is not None:
                return result
        return None

    def find_folder_for_app(self, exe_name: str) -> FolderConfig | None:
        """DFS search for a folder mapped to the given app."""
        exe_lower = exe_name.lower()
        return self._find_folder_for_app(self._config.root_folder, exe_lower)

    def _find_folder_for_app(self, folder: FolderConfig, exe_lower: str) -> FolderConfig | None:
        for app in folder.mapped_apps:
            if app.lower() == exe_lower:
                return folder
        for child in folder.children:
            result = self._find_folder_for_app(child, exe_lower)
            if result is not None:
                return result
        return None

    def add_folder(self, parent_id: str, name: str = "New Folder") -> FolderConfig | None:
        """Create a new sub-folder under parent_id. Returns the new folder or None."""
        parent = self.get_folder_by_id(parent_id)
        if parent is None:
            return None
        new_folder = FolderConfig(
            id=f"folder_{uuid.uuid4().hex[:8]}",
            name=name,
        )
        parent.children.append(new_folder)
        self.save()
        return new_folder

    def rename_folder(self, folder_id: str, new_name: str) -> bool:
        if folder_id == "root":
            return False
        folder = self.get_folder_by_id(folder_id)
        if folder is None:
            return False
        folder.name = new_name
        self.save()
        return True

    def delete_folder(self, folder_id: str) -> bool:
        if folder_id == "root":
            return False
        parent = self.find_parent_folder(folder_id)
        if parent is None:
            return False
        parent.children = [c for c in parent.children if c.id != folder_id]
        self.save()
        return True

    def move_folder(self, folder_id: str, new_parent_id: str, position: int = -1) -> bool:
        """Move a folder to new_parent_id at position. Returns False on cycle or invalid."""
        if folder_id == "root":
            return False
        folder = self.get_folder_by_id(folder_id)
        if folder is None:
            return False
        new_parent = self.get_folder_by_id(new_parent_id)
        if new_parent is None:
            return False

        # Cycle check: new_parent must not be a descendant of folder
        if self._is_descendant(folder, new_parent_id):
            return False

        # Remove from old parent
        old_parent = self.find_parent_folder(folder_id)
        if old_parent is None:
            return False
        old_parent.children = [c for c in old_parent.children if c.id != folder_id]

        # Insert into new parent
        if position < 0 or position >= len(new_parent.children):
            new_parent.children.append(folder)
        else:
            new_parent.children.insert(position, folder)

        self.save()
        return True

    def _is_descendant(self, ancestor: FolderConfig, target_id: str) -> bool:
        """Check if target_id is ancestor itself or a descendant of ancestor."""
        if ancestor.id == target_id:
            return True
        for child in ancestor.children:
            if self._is_descendant(child, target_id):
                return True
        return False

    def export_config(self, path: Path) -> None:
        """Export current config to a JSON file, embedding icon files."""
        data = self._config.to_dict()
        icons = self._collect_icons(data.get("root_folder", {}))
        if icons:
            data["_icons"] = icons
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Config exported to %s", path)

    def import_config(self, path: Path) -> None:
        """Import config from a JSON file, restoring embedded icon files."""
        data = json.loads(path.read_text(encoding="utf-8"))
        icons_data = data.pop("_icons", {})
        if icons_data:
            self._restore_icons(data.get("root_folder", {}), icons_data)
        self._config = AppConfig.from_dict(data)
        self.save()
        logger.info("Config imported from %s", path)

    # --- Folder export/import ---

    @staticmethod
    def _regenerate_folder_ids(folder_dict: dict) -> dict[str, str]:
        """Assign new IDs to all folders and fix internal navigate_folder refs.

        Operates on raw dict (before from_dict) for simplicity.
        Returns the old_id → new_id mapping.
        """
        id_map: dict[str, str] = {}

        # Phase 1: collect old IDs and assign new ones
        def _collect(fd: dict) -> None:
            old_id = fd.get("id", "")
            new_id = f"folder_{uuid.uuid4().hex[:8]}"
            id_map[old_id] = new_id
            fd["id"] = new_id
            for child in fd.get("children", []):
                _collect(child)

        _collect(folder_dict)

        # Phase 2: fix navigate_folder / navigate_page button references
        def _fix_refs(fd: dict) -> None:
            for btn in fd.get("buttons", []):
                action = btn.get("action", {})
                if action.get("type") in ("navigate_folder", "navigate_page"):
                    target = action.get("params", {}).get("folder_id", "")
                    if target in id_map:
                        action["params"]["folder_id"] = id_map[target]
            for child in fd.get("children", []):
                _fix_refs(child)

        _fix_refs(folder_dict)
        return id_map

    @staticmethod
    def _collect_icons(folder_dict: dict) -> dict[str, str]:
        """Collect icon files from a folder dict tree as {basename: base64str}.

        Scans btn["icon"] and btn["action"]["params"] icon keys.
        Only includes files that actually exist on disk.
        """
        icons: dict[str, str] = {}

        def _scan(fd: dict) -> None:
            for btn in fd.get("buttons", []):
                # ButtonConfig.icon
                icon_path = btn.get("icon", "")
                if icon_path:
                    _add_icon(icon_path)
                # ActionConfig.params icon keys
                params = btn.get("action", {}).get("params", {})
                for key in _ICON_PARAM_KEYS:
                    val = params.get(key, "")
                    if val:
                        _add_icon(val)
            for child in fd.get("children", []):
                _scan(child)

        def _add_icon(file_path: str) -> None:
            p = Path(file_path)
            basename = p.name
            if basename in icons:
                return
            if p.is_file():
                try:
                    icons[basename] = base64.b64encode(p.read_bytes()).decode("ascii")
                except Exception:
                    logger.warning("Failed to read icon file: %s", file_path)

        _scan(folder_dict)
        return icons

    @staticmethod
    def _restore_icons(folder_dict: dict, icons_data: dict[str, str]) -> None:
        """Restore icon files from base64 data and rewrite paths in folder dict.

        Writes icons to %APPDATA%/SoftDeck/icons/ and replaces matching
        basenames in btn["icon"] and btn["action"]["params"] icon keys.
        """
        if not icons_data:
            return

        _ICONS_DIR.mkdir(parents=True, exist_ok=True)

        # Write icon files to disk
        local_paths: dict[str, str] = {}
        for basename, b64str in icons_data.items():
            dest = _ICONS_DIR / basename
            if not dest.exists():
                try:
                    dest.write_bytes(base64.b64decode(b64str))
                except Exception:
                    logger.warning("Failed to restore icon: %s", basename)
                    continue
            local_paths[basename] = str(dest)

        # Rewrite paths in folder dict
        def _rewrite(fd: dict) -> None:
            for btn in fd.get("buttons", []):
                icon_path = btn.get("icon", "")
                if icon_path:
                    basename = Path(icon_path).name
                    if basename in local_paths:
                        btn["icon"] = local_paths[basename]
                params = btn.get("action", {}).get("params", {})
                for key in _ICON_PARAM_KEYS:
                    val = params.get(key, "")
                    if val:
                        basename = Path(val).name
                        if basename in local_paths:
                            params[key] = local_paths[basename]
            for child in fd.get("children", []):
                _rewrite(child)

        _rewrite(folder_dict)

    def export_folder(self, folder_id: str, path: Path) -> None:
        """Export a single folder (with children) to a JSON file."""
        folder = self.get_folder_by_id(folder_id)
        if folder is None:
            raise ValueError(f"Folder not found: {folder_id}")
        folder_dict = folder.to_dict()
        envelope: dict = {
            "type": "softdeck_folder",
            "app_version": APP_VERSION,
            "folder": folder_dict,
        }
        icons = self._collect_icons(folder_dict)
        if icons:
            envelope["_icons"] = icons
        path.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Folder '%s' exported to %s", folder.name, path)

    def import_folder(self, parent_id: str, path: Path) -> FolderConfig:
        """Import a folder from a JSON file, appending it to parent_id.

        All folder IDs are regenerated to avoid collisions.
        Embedded icon files are restored to the local icons directory.
        Returns the newly created FolderConfig.
        """
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("type") != "softdeck_folder":
            raise ValueError("Invalid file: not a SoftDeck folder export")
        folder_dict = data.get("folder")
        if not folder_dict or not isinstance(folder_dict, dict):
            raise ValueError("Invalid file: missing folder data")

        self._restore_icons(folder_dict, data.get("_icons", {}))
        self._regenerate_folder_ids(folder_dict)
        new_folder = FolderConfig.from_dict(folder_dict)

        parent = self.get_folder_by_id(parent_id)
        if parent is None:
            raise ValueError(f"Parent folder not found: {parent_id}")
        parent.children.append(new_folder)
        self.save()
        logger.info("Folder '%s' imported under '%s' from %s", new_folder.name, parent.name, path)
        return new_folder

    def get_all_folders_flat(self) -> list[tuple[FolderConfig, int]]:
        """Return flat list of (folder, depth) for combo boxes."""
        result: list[tuple[FolderConfig, int]] = []
        self._collect_folders(self._config.root_folder, 0, result)
        return result

    def _collect_folders(self, folder: FolderConfig, depth: int, result: list[tuple[FolderConfig, int]]) -> None:
        result.append((folder, depth))
        for child in folder.children:
            self._collect_folders(child, depth + 1, result)
