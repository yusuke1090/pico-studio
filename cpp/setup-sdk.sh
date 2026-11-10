#!/bin/sh
# C++ の開発環境（コンパイラと Pico SDK）をまとめて入れる。何回打っても大丈夫。
#   sh ~/apps/pico-studio/cpp/setup-sdk.sh
# 途中で sudo のパスワードを聞かれる（打っても画面には出ない）。
set -e

SDK_VERSION="2.1.1"
SDK_DIR="${PICO_SDK_PATH:-$HOME/pico/pico-sdk}"
STUDIO="$(cd "$(dirname "$0")/.." && pwd)"

echo "== 1/4 コンパイラなどを入れる（apt）"
sudo apt install -y cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib \
    build-essential git python3 libusb-1.0-0-dev pkg-config

echo "== 2/4 Pico SDK $SDK_VERSION をダウンロードする: $SDK_DIR"
if [ -f "$SDK_DIR/pico_sdk_init.cmake" ]; then
    echo "すでにあります（そのまま使います）"
else
    mkdir -p "$(dirname "$SDK_DIR")"
    git clone --branch "$SDK_VERSION" https://github.com/raspberrypi/pico-sdk.git "$SDK_DIR"
fi
# USB の printf に要る TinyUSB などを取ってくる
(cd "$SDK_DIR" && git submodule update --init)

echo "== 3/4 SDK の場所を ~/.bashrc に登録する"
if grep -q "PICO_SDK_PATH" "$HOME/.bashrc" 2>/dev/null; then
    echo "すでに登録されています"
else
    echo "export PICO_SDK_PATH=$SDK_DIR" >> "$HOME/.bashrc"
    echo "登録しました（新しいターミナルから使えます）"
fi

echo "== 4/4 プロジェクトのフォルダ（~/apps/pico-cpp）を用意する"
PICO_SDK_PATH="$SDK_DIR" python3 "$STUDIO/cpp_build.py" init
PICO_SDK_PATH="$SDK_DIR" python3 "$STUDIO/cpp_build.py" check

echo
echo "完了しました。Pico Studio を起動し直す（Ctrl + C → ./start.sh）と、C++ が使えます。"
echo "コマンドでビルドするとき:"
echo "  cd ~/apps/pico-cpp && cmake -S . -B build && make -C build -j4 blink"
