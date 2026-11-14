@echo off
setlocal

cd /d "%~dp0"
set "VENV_DIR=%CD%\.venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "PID_FILE=%CD%\.streamlit.pid"
set "LOG_FILE=%CD%\streamlit.log"

if exist "%PID_FILE%" (
    for /f "usebackq delims=" %%P in ("%PID_FILE%") do set "EXISTING_PID=%%P"
    powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $env:EXISTING_PID) -ErrorAction SilentlyContinue; if ($p -and $p.CommandLine -match 'streamlit.+run.+app\.py') { exit 0 } else { exit 1 }"
    if not errorlevel 1 (
        echo Streamlit is already running with PID %EXISTING_PID%.
        echo Open http://localhost:8501
        exit /b 0
    )
    del /q "%PID_FILE%"
)

if not exist "%PYTHON%" (
    echo Creating Python virtual environment in .venv...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv "%VENV_DIR%"
    ) else (
        where python >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Python 3 was not found. Install Python 3.10 or newer and try again.
            exit /b 1
        )
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        exit /b 1
    )
)

echo Installing/updating dependencies...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist "config.yaml" (
    if not exist "config.example.yaml" (
        echo ERROR: config.yaml and config.example.yaml are both missing.
        exit /b 1
    )
    copy /y "config.example.yaml" "config.yaml" >nul
    echo Created config.yaml from config.example.yaml. Review it before using the pipeline.
)

echo Starting Streamlit...
powershell -NoProfile -Command "$p = Start-Process -FilePath $env:PYTHON -ArgumentList '-m','streamlit','run','app.py','--server.headless=true' -WorkingDirectory (Get-Location) -RedirectStandardOutput $env:LOG_FILE -RedirectStandardError ($env:LOG_FILE + '.err') -PassThru; Set-Content -LiteralPath $env:PID_FILE -Value $p.Id -NoNewline; Write-Output $p.Id"
if errorlevel 1 (
    echo ERROR: Streamlit failed to start.
    exit /b 1
)

echo Streamlit is starting at http://localhost:8501
echo Logs: streamlit.log and streamlit.log.err
echo Run stop.bat to stop it.
endlocal
