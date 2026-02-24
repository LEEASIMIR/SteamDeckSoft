@echo off
echo === SteamDeckSoft Build ===

pyinstaller --noconfirm --onefile --windowed ^
    --name SteamDeckSoft ^
    --add-data "config;config" ^
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
