import ctypes
import sys

_instance_mutex = None


def _check_single_instance() -> bool:
    """Win32 Named Mutex로 단일 인스턴스 체크. QApplication 생성 전에 호출해야 함."""
    global _instance_mutex
    kernel32 = ctypes.windll.kernel32
    _instance_mutex = kernel32.CreateMutexW(None, False, "SteamDeckSoft_SingleInstance")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(_instance_mutex)
        _instance_mutex = None
        return False
    return True


def main() -> int:
    if not _check_single_instance():
        print("SteamDeckSoft is already running.")
        return 1

    from src.app import SteamDeckSoftApp

    app = SteamDeckSoftApp(sys.argv)

    try:
        exit_code = app.exec()
    finally:
        app.cleanup()
        if _instance_mutex:
            ctypes.windll.kernel32.CloseHandle(_instance_mutex)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
