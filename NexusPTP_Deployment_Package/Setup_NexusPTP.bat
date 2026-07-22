@echo off
title NexusPTP - Setup & Desktop Shortcut Creator
echo ===================================================
echo   NexusPTP - Payment & Contract Tracking System
echo   Deployment Setup Script for DICT Computers
echo ===================================================
echo.

set TARGET_DIR=%CD%
set EXE_PATH=%TARGET_DIR%\NexusPTP.exe
set SHORTCUT_PATH=%USERPROFILE%\Desktop\NexusPTP.lnk

if not exist "%EXE_PATH%" (
    echo [ERROR] NexusPTP.exe was not found in %TARGET_DIR%!
    echo Please make sure you extract all files before running this script.
    pause
    exit /b 1
)

echo Creating Desktop Shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath='%EXE_PATH%'; $s.WorkingDirectory='%TARGET_DIR%'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [SUCCESS] Desktop Shortcut created successfully on your Desktop!
) else (
    echo [WARNING] Could not create Desktop Shortcut automatically. You can launch NexusPTP.exe directly from this folder.
)

echo.
echo Setup completed! You may now double-click NexusPTP on your Desktop to run the app.
echo.
pause
