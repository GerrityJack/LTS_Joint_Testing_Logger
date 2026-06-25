@echo off
chcp 65001 >nul
SETLOCAL
TITLE Create Desktop Shortcut

echo.
echo  ============================================================
echo   Creating Desktop Shortcut for LakeShore/Keithley Logging
echo  ============================================================
echo.

SET "LAB_DIR=%~dp0"
IF "%LAB_DIR:~-1%"=="\" SET "LAB_DIR=%LAB_DIR:~0,-1%"

SET "SHORTCUT_PATH=%USERPROFILE%\Desktop\Start Temp and SMU Logging.lnk"
SET "TARGET_PATH=%LAB_DIR%\startup.bat"

IF NOT EXIST "%TARGET_PATH%" (
    echo  ERROR: startup.bat not found at:
    echo         %TARGET_PATH%
    echo  Run this script from the same folder as startup.bat.
    pause
    exit /b 1
)

IF EXIST "%SHORTCUT_PATH%" (
    echo  Existing shortcut found - it will be overwritten.
)

powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$sc = $ws.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$sc.TargetPath = '%TARGET_PATH%'; " ^
    "$sc.WorkingDirectory = '%LAB_DIR%'; " ^
    "$sc.IconLocation = 'cmd.exe,0'; " ^
    "$sc.Description = 'Start LakeShore 218 / Keithley 2401 Logging'; " ^
    "$sc.Save()"

IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Failed to create shortcut.
    pause
    exit /b 1
)

echo  OK - Shortcut created/updated at:
echo       %SHORTCUT_PATH%
echo.
echo  You can now double-click "Start Temp and SMU Logging" on your Desktop
echo  to launch QuestDB and both logging scripts.
echo.
pause
