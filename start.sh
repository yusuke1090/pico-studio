#!/bin/sh
# Pico Studio を起動して、ブラウザで開く
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
URL="http://localhost:$PORT"

# すでに起動していれば、ブラウザで開くだけにする
if curl -s -o /dev/null --max-time 1 "$URL/api/state"; then
    # C++ モードより前のサーバーが動いたままなら、起動し直してもらう
    if curl -s --max-time 1 "$URL/api/cpp/env" | grep -q '"error": "not found"'; then
        echo "古い Pico Studio が動いています（C++ モードが使えません）。"
        echo "起動したターミナルで Ctrl + C を押して止めてから、もう一度 ./start.sh を打ってください。"
        echo "ターミナルがわからないときは: pkill -f 'pico-studio/server.py'"
        exit 1
    fi
    echo "Pico Studio はすでに起動しています: $URL"
    xdg-open "$URL" >/dev/null 2>&1
    exit 0
fi

( sleep 1; xdg-open "$URL" >/dev/null 2>&1 ) &
exec python3 server.py --port "$PORT"
