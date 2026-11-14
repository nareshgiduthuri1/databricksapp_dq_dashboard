@echo off
setlocal

cd /d "%~dp0"
set "PID_FILE=%CD%\.streamlit.pid"
set "EXPECTED_PYTHON=%CD%\.venv\Scripts\python.exe"

if not exist "%PID_FILE%" (
    echo Streamlit is not running ^(no .streamlit.pid file^).
    exit /b 0
)

set /p STREAMLIT_PID=<"%PID_FILE%"
powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $env:STREAMLIT_PID) -ErrorAction SilentlyContinue; if (-not $p) { exit 2 }; if ($p.ExecutablePath -ne $env:EXPECTED_PYTHON -or $p.CommandLine -notmatch 'streamlit.+run.+app\.py') { exit 3 }; Stop-Process -Id $p.ProcessId -Force"
set "STOP_RESULT=%ERRORLEVEL%"

if "%STOP_RESULT%"=="2" (
    echo The recorded process is no longer running. Removing the stale PID file.
    del /q "%PID_FILE%"
    exit /b 0
)
if "%STOP_RESULT%"=="3" (
    echo ERROR: PID %STREAMLIT_PID% belongs to another process; it was not stopped.
    echo Remove .streamlit.pid manually after verifying the process.
    exit /b 1
)
if not "%STOP_RESULT%"=="0" (
    echo ERROR: Could not stop Streamlit process %STREAMLIT_PID%.
    exit /b 1
)

del /q "%PID_FILE%"
echo Streamlit stopped.
endlocal
