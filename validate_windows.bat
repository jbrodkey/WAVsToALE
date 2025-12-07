@echo off
REM Automated validation script for WAVsToALE Windows build

SET EXE_PATH=dist\WAVsToALE.exe
SET README_PATH=dist\WAVsToALE\README.md

REM 1. Check if executable exists
IF NOT EXIST "%EXE_PATH%" (
    echo Error: Executable not found at %EXE_PATH%
    exit /b 1
)
echo Executable found: %EXE_PATH%

REM 2. Check if README exists in distribution folder
IF NOT EXIST "%README_PATH%" (
    echo Warning: README.md not found in distribution folder.
) ELSE (
    echo README.md found in distribution folder.
)

REM 3. Attempt to launch the app (headless)
start "WAVsToALE" /B "%EXE_PATH%"
REM Wait a moment and check if process started
ping 127.0.0.1 -n 3 > nul
REM Check if process is running
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq WAVsToALE.exe" /NH') do (
    if "%%a" NEQ "" (
        echo App launched successfully (PID: %%a)
        taskkill /F /PID %%a
    ) else (
        echo Warning: App did not launch (may require GUI).
    )
)

echo Validation complete.
