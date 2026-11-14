#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"
PID_FILE="$SCRIPT_DIR/.streamlit.pid"
LOG_FILE="$SCRIPT_DIR/streamlit.log"

if [ -f "$PID_FILE" ]; then
    existing_pid=$(cat "$PID_FILE")
    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
        existing_command=$(ps -p "$existing_pid" -o command= 2>/dev/null || true)
        case "$existing_command" in
            *streamlit*run*app.py*)
                echo "Streamlit is already running with PID $existing_pid."
                echo "Open http://localhost:8501"
                exit 0
                ;;
        esac
    fi
    rm -f "$PID_FILE"
fi

if [ ! -x "$PYTHON" ]; then
    echo "Creating Python virtual environment in .venv..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv "$VENV_DIR"
    elif command -v python >/dev/null 2>&1; then
        python -m venv "$VENV_DIR"
    else
        echo "ERROR: Python 3 was not found. Install Python 3.10 or newer and try again." >&2
        exit 1
    fi
fi

echo "Installing/updating dependencies..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements.txt

if [ ! -f config.yaml ]; then
    if [ ! -f config.example.yaml ]; then
        echo "ERROR: config.yaml and config.example.yaml are both missing." >&2
        exit 1
    fi
    cp config.example.yaml config.yaml
    echo "Created config.yaml from config.example.yaml. Review it before using the pipeline."
fi

echo "Starting Streamlit..."
nohup "$PYTHON" -m streamlit run app.py --server.headless=true >"$LOG_FILE" 2>&1 &
streamlit_pid=$!
printf '%s' "$streamlit_pid" >"$PID_FILE"

sleep 2
if ! kill -0 "$streamlit_pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "ERROR: Streamlit exited during startup. Check streamlit.log." >&2
    exit 1
fi

echo "Streamlit is starting at http://localhost:8501"
echo "Logs: streamlit.log"
echo "Run ./stop.sh to stop it."
