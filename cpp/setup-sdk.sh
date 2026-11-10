#!/bin/sh
# C++ の開発環境（コンパイラと Pico SDK）をまとめて入れる。何回打っても大丈夫。
#   sh ~/apps/pico-studio/cpp/setup-sdk.sh
# 途中で sudo のパスワードを聞かれる（打っても画面には出ない）。
set -e

SDK_VERSION="2.1.1"
SDK_DIR="${PICO_SDK_PATH:-$HOME/pico/pico-sdk}"
STUDIO="$(cd "$(dirname "$0")/.." && pwd)"

echo "== 1/5 コンパイラなどを入れる（apt）"
sudo apt install -y cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib \
    build-essential git python3 libusb-1.0-0-dev pkg-config

echo "== 2/5 Pico SDK $SDK_VERSION をダウンロードする: $SDK_DIR"
if [ -f "$SDK_DIR/pico_sdk_init.cmake" ]; then
    echo "すでにあります（そのまま使います）"
else
    mkdir -p "$(dirname "$SDK_DIR")"
    git clone --branch "$SDK_VERSION" https://github.com/raspberrypi/pico-sdk.git "$SDK_DIR"
fi
# USB の printf に要る TinyUSB などを取ってくる
(cd "$SDK_DIR" && git submodule update --init)

echo "== 3/5 SDK の場所を ~/.bashrc に登録する"
if grep -q "PICO_SDK_PATH" "$HOME/.bashrc" 2>/dev/null; then
    echo "すでに登録されています"
else
    echo "export PICO_SDK_PATH=$SDK_DIR" >> "$HOME/.bashrc"
    echo "登録しました（新しいターミナルから使えます）"
fi

echo "== 4/5 プロジェクトのフォルダ（~/apps/pico-cpp）を用意する"
PICO_SDK_PATH="$SDK_DIR" python3 "$STUDIO/cpp_build.py" init
PICO_SDK_PATH="$SDK_DIR" python3 "$STUDIO/cpp_build.py" check

echo "== 5/5 picotool（USB でピコを操作するツール）を入れる: ~/.local/bin/picotool"
# SDK がビルドの途中で作る picotool は USB の機能なしなので、別にビルドする
PT_VERSION="$SDK_VERSION"
PT_SRC="$(dirname "$SDK_DIR")/picotool"
if command -v picotool >/dev/null 2>&1 && ! picotool version 2>&1 | grep -q "without USB"; then
    echo "すでにあります: $(command -v picotool)"
else
    [ -d "$PT_SRC" ] || git clone --branch "$PT_VERSION" https://github.com/raspberrypi/picotool.git "$PT_SRC"
    # CMAKE_POLICY_VERSION_MINIMUM: SDK の中の mbedtls が古い書き方なので、CMake 4 以降でも通るようにする
    # -Wno-dev: picotool を作る人向けの注意（動きには関係ない）を出さない
    cmake -S "$PT_SRC" -B "$PT_SRC/build" -DPICO_SDK_PATH="$SDK_DIR" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -Wno-dev
    make -C "$PT_SRC/build" -j4 picotool
    mkdir -p "$HOME/.local/bin"
    cp "$PT_SRC/build/picotool" "$HOME/.local/bin/picotool"
    echo "入れました: $HOME/.local/bin/picotool"
fi
# sudo なしで picotool がピコを操作できるようにする（udev ルール）
if [ ! -f /etc/udev/rules.d/60-picotool.rules ] && [ -f "$PT_SRC/udev/60-picotool.rules" ]; then
    sudo cp "$PT_SRC/udev/60-picotool.rules" /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    echo "udev ルールを入れました（ピコを一度抜いて、つなぎ直してください）"
fi

echo
echo "完了しました。Pico Studio を起動し直す（Ctrl + C → ./start.sh）と、C++ が使えます。"
echo "コマンドでビルドするとき:"
echo "  cd ~/apps/pico-cpp && cmake -S . -B build && make -C build -j4 blink"
echo "picotool は新しいターミナルから使えます（picotool version で確かめる）"
