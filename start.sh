#!/bin/sh
# Pico Studio を起動して、ブラウザで開く
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
URL="http://localhost:$PORT"
( sleep 1; xdg-open "$URL" >/dev/null 2>&1 ) &
exec python3 server.py --port "$PORT"
