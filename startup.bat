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

SET "QUESTDB_EXE=C:\Users\scuser\questdb\questdb-9.4.3-rt-windows-x86-64\bin\questdb.exe"
SET QUESTDB_PORT=9000
SET QUESTDB_WAIT=8
SET DRIVER_WAIT=3

:: -- Step 1: Check / start QuestDB --------------------------------------------
echo [1/3] Checking QuestDB...

powershell -NoProfile -Command "$c = New-Object Net.Sockets.TcpClient; try { $c.Connect('localhost', %QUESTDB_PORT%); $c.Close(); exit 0 } catch { exit 1 }"

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
echo  Waiting %QUESTDB_WAIT%s for QuestDB to become ready...
timeout /t %QUESTDB_WAIT% /nobreak >nul

powershell -NoProfile -Command "$c = New-Object Net.Sockets.TcpClient; try { $c.Connect('localhost', %QUESTDB_PORT%); $c.Close(); exit 0 } catch { exit 1 }"

IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: QuestDB still not reachable on port %QUESTDB_PORT% after waiting.
    echo         Check the QuestDB window for errors.
    goto :FATAL
)
echo  OK - QuestDB is now running.

:QUESTDB_DONE
echo.

:: -- Step 2: Start LakeShore 218 logger ---------------------------------------
echo [2/3] Starting LakeShore 218 logger...

powershell -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*lakeshore218_logger.py*' }; if ($procs) { exit 1 } else { exit 0 }"

IF %ERRORLEVEL% EQU 1 (
    echo  INFO: LakeShore 218 logger is already running - skipping to prevent duplicates.
) ELSE (
    start "LakeShore 218 Logger" /D "%LAB_DIR%" /MIN cmd /k python lakeshore218_logger.py
    timeout /t %DRIVER_WAIT% /nobreak >nul
    echo  OK - LakeShore 218 logger launched (check its window for hardware errors).
)
echo.

:: -- Step 3: Start Keithley 2401 logger ---------------------------------------
echo [3/3] Starting Keithley 2401 logger...

powershell -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*keithley2401_logger.py*' }; if ($procs) { exit 1 } else { exit 0 }"

IF %ERRORLEVEL% EQU 1 (
    echo  INFO: Keithley 2401 logger is already running - skipping to prevent duplicates.
) ELSE (
    start "Keithley 2401 Logger" /D "%LAB_DIR%" /MIN cmd /k python keithley2401_logger.py
    timeout /t %DRIVER_WAIT% /nobreak >nul
    echo  OK - Keithley 2401 logger launched (check its window for hardware errors).
)
echo.

echo  ============================================================
echo   Startup complete. QuestDB and both loggers are running in
echo   minimized background windows. This window will close itself.
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
