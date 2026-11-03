#!/bin/sh
# Pico Studio を起動して、ブラウザで開く
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
URL="http://localhost:$PORT"

# すでに起動していれば、ブラウザで開くだけにする
if curl -s -o /dev/null --max-time 1 "$URL/api/state"; then
    echo "Pico Studio はすでに起動しています: $URL"
    xdg-open "$URL" >/dev/null 2>&1
    exit 0
fi

( sleep 1; xdg-open "$URL" >/dev/null 2>&1 ) &
exec python3 server.py --port "$PORT"
