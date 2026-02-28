import sys


def main() -> int:
    from src.app import SoftDeckApp

    app = SoftDeckApp(sys.argv)

    try:
        exit_code = app.exec()
    finally:
        app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
