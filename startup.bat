@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
TITLE LakeShore 218 / Keithley 2401 Logging - System Startup
COLOR 0A

echo.
echo  ============================================================
echo   LakeShore 218 / Keithley 2401 Logging - System Startup
echo   %DATE%  %TIME%
echo  ============================================================
echo.

:: -- Configuration -----------------------------------------------------------
SET "LAB_DIR=%~dp0"
IF "%LAB_DIR:~-1%"=="\" SET "LAB_DIR=%LAB_DIR:~0,-1%"

SET "QUESTDB_EXE=C:\Users\scuser\Program\questdb\bin\questdb.exe"
SET QUESTDB_PORT=9000

SET "GRAFANA_HOME=C:\Users\scuser\Program\grafana"
SET "GRAFANA_EXE=C:\Users\scuser\Program\grafana\bin\grafana-server.exe"
SET GRAFANA_PORT=3000

SET SERVICE_WAIT=8
SET DRIVER_WAIT=3

:: -- Step 1: Check / start QuestDB --------------------------------------------
echo [1/4] Checking QuestDB...

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_port.ps1" -Port %QUESTDB_PORT%

IF %ERRORLEVEL% EQU 0 (
    echo  OK - QuestDB is already running on port %QUESTDB_PORT%.
    goto :QUESTDB_DONE
)

echo  QuestDB not detected - starting it...
IF NOT EXIST "%QUESTDB_EXE%" (
    echo  ERROR: QuestDB executable not found at:
    echo         %QUESTDB_EXE%
    echo  Edit QUESTDB_EXE at the top of this script if it has moved.
    goto :FATAL
)

start "QuestDB" /MIN "%QUESTDB_EXE%" start
echo  Waiting %SERVICE_WAIT%s for QuestDB to become ready...
timeout /t %SERVICE_WAIT% /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_port.ps1" -Port %QUESTDB_PORT%

IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: QuestDB still not reachable on port %QUESTDB_PORT% after waiting.
    echo         Check the QuestDB window for errors.
    goto :FATAL
)
echo  OK - QuestDB is now running.

:QUESTDB_DONE
echo.

:: -- Step 2: Check / start Grafana ---------------------------------------------
echo [2/4] Checking Grafana...

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_port.ps1" -Port %GRAFANA_PORT%

IF %ERRORLEVEL% EQU 0 (
    echo  OK - Grafana is already running on port %GRAFANA_PORT%.
    goto :GRAFANA_DONE
)

echo  Grafana not detected - starting it...
IF NOT EXIST "%GRAFANA_EXE%" (
    echo  ERROR: Grafana executable not found at:
    echo         %GRAFANA_EXE%
    echo  Edit GRAFANA_EXE at the top of this script if it has moved.
    goto :FATAL
)

start "Grafana" /D "%GRAFANA_HOME%" /MIN "%GRAFANA_EXE%"
echo  Waiting %SERVICE_WAIT%s for Grafana to become ready...
timeout /t %SERVICE_WAIT% /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_port.ps1" -Port %GRAFANA_PORT%

IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Grafana still not reachable on port %GRAFANA_PORT% after waiting.
    echo         Check the Grafana window for errors.
    goto :FATAL
)
echo  OK - Grafana is now running.

:GRAFANA_DONE
echo.

:: -- Step 3: Start LakeShore 218 logger ---------------------------------------
echo [3/4] Starting LakeShore 218 logger...

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_process_running.ps1" -ScriptName lakeshore218_logger.py

IF %ERRORLEVEL% EQU 1 (
    echo  INFO: LakeShore 218 logger is already running - skipping to prevent duplicates.
) ELSE (
    start "LakeShore 218 Logger" /D "%LAB_DIR%" /MIN cmd /k python lakeshore218_logger.py
    timeout /t %DRIVER_WAIT% /nobreak >nul
    echo  OK - LakeShore 218 logger launched (check its window for hardware errors).
)
echo.

:: -- Step 4: Start Keithley 2401 logger ---------------------------------------
echo [4/4] Starting Keithley 2401 logger...

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAB_DIR%\check_process_running.ps1" -ScriptName keithley2401_logger.py

IF %ERRORLEVEL% EQU 1 (
    echo  INFO: Keithley 2401 logger is already running - skipping to prevent duplicates.
) ELSE (
    start "Keithley 2401 Logger" /D "%LAB_DIR%" /MIN cmd /k python keithley2401_logger.py
    timeout /t %DRIVER_WAIT% /nobreak >nul
    echo  OK - Keithley 2401 logger launched (check its window for hardware errors).
)
echo.

echo  ============================================================
echo   Startup complete. QuestDB, Grafana, and both loggers are
echo   running in minimized background windows. This window will
echo   close itself.
echo  ============================================================
timeout /t 3 /nobreak >nul
ENDLOCAL
exit /b 0

:FATAL
echo.
echo  ============================================================
echo   STARTUP FAILED - see error above.
echo  ============================================================
pause
ENDLOCAL
exit /b 1
