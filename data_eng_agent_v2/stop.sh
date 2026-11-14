#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PID_FILE="$SCRIPT_DIR/.streamlit.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Streamlit is not running (no .streamlit.pid file)."
    exit 0
fi

streamlit_pid=$(cat "$PID_FILE")
if [ -z "$streamlit_pid" ] || ! kill -0 "$streamlit_pid" 2>/dev/null; then
    echo "The recorded process is no longer running. Removing the stale PID file."
    rm -f "$PID_FILE"
    exit 0
fi

process_command=$(ps -p "$streamlit_pid" -o command= 2>/dev/null || true)
case "$process_command" in
    *"$SCRIPT_DIR/.venv/bin/python"*streamlit*run*app.py*) ;;
    *)
        echo "ERROR: PID $streamlit_pid belongs to another process; it was not stopped." >&2
        echo "Remove .streamlit.pid manually after verifying the process." >&2
        exit 1
        ;;
esac

kill "$streamlit_pid"
i=0
while kill -0 "$streamlit_pid" 2>/dev/null && [ "$i" -lt 10 ]; do
    sleep 1
    i=$((i + 1))
done

if kill -0 "$streamlit_pid" 2>/dev/null; then
    echo "Streamlit did not exit cleanly; forcing it to stop."
    kill -9 "$streamlit_pid"
fi

rm -f "$PID_FILE"
echo "Streamlit stopped."
