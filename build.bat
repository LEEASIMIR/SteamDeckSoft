@echo off
echo === SteamDeckSoft Build ===

pyinstaller --noconfirm --clean --onefile --windowed ^
    --name SteamDeckSoft ^
    --add-data "config;config" ^
    --add-binary "src\native\numpad_hook.dll;." ^
    --hidden-import comtypes.stream ^
    --hidden-import pycaw.utils ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build complete: dist\SteamDeckSoft.exe
) else (
    echo.
    echo Build failed!
)
pause
