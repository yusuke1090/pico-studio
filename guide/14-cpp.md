# 14. C++ の開発環境と基本

## この章でわかること

- MicroPython と C++ の進め方の違い
- PC に C++ の開発環境（Pico SDK とコンパイラ）を用意する手順
- Pico Studio が C++ をどうビルドして書き込んでいるか
- Pico Studio を使わずに、コマンドでビルドする方法（CMake）
- MicroPython の書き方と C++ の書き方の対応
- MicroPython に戻す方法

C++ の文法の基本（変数・関数・クラス）がわかる前提で書いています。ここでは Raspberry Pi 公式の **Pico SDK** を使います。
個別の使い方（LED・ボタン・ADC・I2C センサー・データの記録・機械学習）は、4〜10章を C++ に切り替えて読んでください。
C++ だけの話は、次の章にあります。

| 章 | 内容 |
| --- | --- |
| 15章 | マイコン向けの C++ の書き方（型、メモリ、クラス、ファイルの分け方） |
| 16章 | 割り込み・タイマー・2つのコア |
| 17章 | 省電力とウォッチドッグ、設定の保存 |
| 18章 | 製品にするための準備（テスト、デバッグ、量産の書き込み） |

## MicroPython との違い

| 項目 | MicroPython | C++（Pico SDK） |
| --- | --- | --- |
| 動かすまで | コードを送れば、すぐ動く | PC でビルドして、.uf2 を書き込む |
| 速さ | 遅い | 10〜100 倍速い |
| ピコに入っているもの | MicroPython と、自分の .py ファイル | 自分のプログラムだけ（.uf2 にまとまっている） |
| 対話で試す（REPL） | できる | できない |
| ファイルの保存 | `open()` でピコに保存できる | ファイルのしくみがない。フラッシュに数値のまま書くか、PC に送る（9章） |
| `print` の出力 | Pico Studio の出力欄 | `printf`。Pico Studio の出力欄か、シリアルモニター（この章の「出力を見る」） |
| Pico Studio | 「▶ 実行」ですぐ動く | 「▶ ビルドして書き込む」でビルドから書き込みまで自動 |
| 起動時に動かす | `main.py` を置く | 書き込んだプログラムが、電源を入れると必ず動く |

**C++ のプログラムを書き込むと、MicroPython は消えます。** MicroPython に戻すときは、もう一度 MicroPython を書き込みます（この章の「MicroPython に戻す」）。

おすすめの進め方は、**MicroPython で試して、決まった処理を C++ に書き直す**ことです。
配線やセンサーの確認、データ集めは MicroPython のほうが早く進みます。

### もう1つの方法: arduino-pico

Arduino の書き方（`setup()` と `loop()`）で C++ を書く **arduino-pico** という方法もあります（3章のリンク参照）。

| | Pico SDK（この章） | arduino-pico |
| --- | --- | --- |
| 作っているところ | Raspberry Pi 公式 | 有志 |
| ビルド | CMake とコマンド | Arduino IDE や arduino-cli |
| ライブラリ | ピコの機能を細かく使える | Arduino 用のセンサーのライブラリがそのまま使える |
| 向いている人 | Linux のコマンドに慣れている。細かく制御したい | Arduino を使ったことがある |

## 開発環境を用意する（最初の1回だけ）

Ubuntu の場合です。PC のターミナルで行います。

### まとめて入れる（おすすめ）

次のコマンドを打つと、下の 1〜3 と、プロジェクトのフォルダ（`~/apps/pico-cpp`）の用意まで、まとめて行います。途中でパスワードを聞かれます（打っても画面には出ません）。

```bash
sh ~/apps/pico-studio/cpp/setup-sdk.sh
```

最後に `OK: C++ でビルドできます` と出れば完了です。ターミナルを開き直してから使います。
何回打っても大丈夫です（あるものはそのまま使い、足りないものだけを足します）。
終わったら Pico Studio を起動し直す（Ctrl + C → `./start.sh`）と、「接続の確認」の「C++ の開発環境」が緑になります。

足りないものだけを確かめたいときは、次のコマンドを打ちます。

```bash
python3 ~/apps/pico-studio/cpp_build.py check
```

### このスクリプトがすること

スクリプトは、上から順に次の5つを行います。中身は `~/apps/pico-studio/cpp/setup-sdk.sh` で読めます。

| 順番 | すること | 入る場所 | 中身 |
| --- | --- | --- | --- |
| 1/5 | コンパイラなどを入れる（`sudo apt install`） | `/usr/bin` など（PC 全体） | 下の「1. コンパイラなどを入れる」の表のパッケージ |
| 2/5 | Pico SDK 2.1.1 をダウンロードする（`git clone` と `git submodule update --init`） | `~/pico/pico-sdk` | SDK 本体と、SDK が使うライブラリ（下の表） |
| 3/5 | SDK の場所を登録する | `~/.bashrc` の最後に1行 | `export PICO_SDK_PATH=/home/ユーザー名/pico/pico-sdk` |
| 4/5 | プロジェクトのフォルダを用意して、そろったか確かめる | `~/apps/pico-cpp` | `CMakeLists.txt`、`pico_sdk_import.cmake`、`.gitignore`、`blink.cpp`、`mpu6050.h`、`ws2812.h` |
| 5/5 | picotool を作って入れる（`git clone` してビルド）。sudo なしで使えるように udev ルールも入れる | `~/pico/picotool`（ソース）、`~/.local/bin/picotool`、`/etc/udev/rules.d/60-picotool.rules` | USB でピコを書き込みモードにする・書き込む・中を調べるツール（2章・18章）。なくてもビルドと Pico Studio の書き込みはできる |

SDK と一緒にダウンロードされるライブラリ（サブモジュール）は次のとおりです。

| ライブラリ | 使い道 |
| --- | --- |
| TinyUSB | USB のしくみ。`printf` を USB で PC に送るのに使う（**必須**） |
| cyw43-driver | Pico W の無線のチップを動かす |
| lwIP | Pico W で WiFi の通信（TCP/IP）をする |
| BTstack | Pico W で Bluetooth を使う |
| mbedtls | 暗号（HTTPS など） |

- ダウンロードとインストールで、合わせて **1GB 前後**のディスクを使います（目安です）。インターネットにつながっている必要があります
- `~/.bashrc` に書いた1行は、**新しく開いたターミナル**から効きます。開いたままのターミナルでは `source ~/.bashrc` を打つか、開き直します
- 3/5 は、`~/.bashrc` にすでに `PICO_SDK_PATH` があれば何もしません。SDK を別の場所に置きたいときは、`PICO_SDK_PATH=/置きたい場所 sh ~/apps/pico-studio/cpp/setup-sdk.sh` のように打ちます
- 4/5 は、すでにあるファイルを上書きしません
- 5/5 は、USB の機能がある picotool がすでにあれば何もしません

### あとからできるもの

スクリプトのあと、初めてビルドしたときに、次のものが自動でできます。

| もの | 場所 | 中身 |
| --- | --- | --- |
| Pico Studio のビルド用のフォルダ | `~/.cache/pico-studio/cpp` | 「▶ ビルドして書き込む」で使う。消しても、次のビルドで作り直す |
| コマンドでビルドしたもの | `~/apps/pico-cpp/build` | `.uf2` など。消しても `cmake` からやり直せる |
| picotool（`.uf2` を作る用） | それぞれの `build/_deps` の中 | ビルドのときに SDK が自動でダウンロードして作る（インターネットが必要）。USB の機能はないので、ピコの操作には 5/5 で入れた picotool を使う |

### 元に戻すとき

C++ の開発環境を消したいときは、次のようにします。

```bash
rm -rf ~/pico/pico-sdk ~/pico/picotool ~/.local/bin/picotool ~/.cache/pico-studio
sudo rm /etc/udev/rules.d/60-picotool.rules
sudo apt remove gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib
```

`~/.bashrc` の `export PICO_SDK_PATH=...` の行は、テキストエディタで開いて消します（`nano ~/.bashrc`）。
`~/apps/pico-cpp` には自分で書いたプログラムが入っているので、消すときは中身を確かめてからにします。

### 1つずつ入れる

スクリプトを使わずに、自分で1つずつ入れるときの手順です。スクリプトの 1/5〜3/5 と同じことをします（picotool の作り方は [picotool の README](https://github.com/raspberrypi/picotool) を見てください）。

#### 1. コンパイラなどを入れる

```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib build-essential git python3 libusb-1.0-0-dev pkg-config
```

| パッケージ | 役割 |
| --- | --- |
| `cmake` | ビルドの手順を作るソフト |
| `gcc-arm-none-eabi` | ピコ（ARM）用のコンパイラ。PC の `g++` ではピコのプログラムは作れない |
| `libnewlib-arm-none-eabi`、`libstdc++-arm-none-eabi-newlib` | ピコ用の C / C++ の標準ライブラリ |
| `build-essential` | `make` など、ビルドに使う基本の道具 |
| `git` | SDK のダウンロードに使う |
| `python3` | SDK のビルドの途中で使う。Pico Studio にも必要 |
| `libusb-1.0-0-dev`、`pkg-config` | ビルドのときに picotool（ピコを操作するツール）を自動で作るのに使う |

#### 2. Pico SDK をダウンロードする

```bash
mkdir -p ~/pico
cd ~/pico
git clone --branch 2.1.1 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
```

- `--branch 2.1.1` はバージョンの指定です。新しいバージョンは [リリースのページ](https://github.com/raspberrypi/pico-sdk/releases) で確かめられます
- `git submodule update --init` は、SDK が使う USB のライブラリ（TinyUSB）などをダウンロードします。**これを忘れると、USB で `printf` が出ません**

#### 3. SDK の場所を登録する

ビルドのときに SDK の場所がわかるように、`~/.bashrc` に書いておきます。

```bash
echo 'export PICO_SDK_PATH=~/pico/pico-sdk' >> ~/.bashrc
source ~/.bashrc
```

> VS Code を使っているなら、拡張機能の **Raspberry Pi Pico** を入れると、ここまでの準備とビルド・書き込みをボタンでできます。
> この章では、何が起きているかわかるように、コマンドで進めます。

## Pico Studio で確かめる

1. Pico Studio を起動し（すでに起動していたら、ブラウザを再読み込み）、コード欄で **C++** を選ぶ
2. 「接続の確認」の3つ目の **「C++ の開発環境」** が緑になり、Pico SDK のバージョンが出れば準備完了
3. 「サンプルを選ぶ」→「LED を点滅させる」→「▶ ビルドして書き込む」
4. 1回目は SDK 全体をビルドするので数分かかる。ボードの LED が点滅し、出力欄に `LED ON` / `LED OFF` が出れば成功

Pico Studio は、SDK を `~/pico/pico-sdk`（または環境変数 `PICO_SDK_PATH`）から探します。

## Pico Studio のビルドのしくみ

「▶ ビルドして書き込む」を押すと、Pico Studio は次のことを自動で行います。

1. コード欄のコードを、`~/.cache/pico-studio/cpp/app/main.cpp` に書く
2. 同じフォルダに `CMakeLists.txt` を作り、`cmake`（初回とボードを変えたとき）と `make` でビルドする
3. ピコを書き込みモードにする
   - MicroPython が動いていれば、`machine.bootloader()` を送る
   - C++ のプログラムが動いていれば、ポートを 1200 bps で開いて閉じる（Pico SDK の決まり。`stdio_init_all()` を呼んでいるプログラムだけ）
4. `RPI-RP2` ドライブに `app.uf2` をコピーする
5. ピコが再起動したら、シリアルポートにつないで `printf` の出力を表示する

Pico Studio のビルドでは、次の設定が最初から入っています。

| 項目 | 内容 |
| --- | --- |
| 使えるライブラリ | `pico_stdlib`、`hardware_adc`、`hardware_i2c`、`hardware_spi`、`hardware_pwm`、`hardware_uart`、`hardware_pio`、`hardware_dma`、`hardware_flash`、`hardware_watchdog`、`hardware_clocks`、`hardware_sync`、`hardware_timer`、`hardware_irq`、`pico_multicore`、`pico_unique_id`（Pico W では `pico_cyw43_arch_none` も） |
| `#include "…"` を探す場所 | Pico Studio に入っているヘッダー（`mpu6050.h`、`ws2812.h`）と、`~/apps/pico-cpp` |
| `printf` の出力先 | USB（`pico_enable_stdio_usb`） |
| C++ のバージョン | C++17 |

使わないライブラリは、ビルドのときに自動で取り除かれるので、プログラムは大きくなりません。
ここにないライブラリ（Pico W の無線で TCP/IP を使う `pico_cyw43_arch_lwip_*` など）や、PIO のプログラム（`.pio`）を使いたいときは、次の「コマンドでビルドする」の方法で、自分で `CMakeLists.txt` を書きます。

## コマンドでビルドする

製品のプログラムは、複数のファイルに分けたり、git で管理したりします。そのときは、自分でプロジェクトのフォルダと `CMakeLists.txt` を作り、コマンドでビルドします。

### プロジェクトのフォルダを作る

```bash
python3 ~/apps/pico-studio/cpp_build.py init
```

`~/apps/pico-cpp` に、ビルドに必要なファイルができます（「まとめて入れる」のスクリプトを使った人は、もうできています）。
すでにあるファイルは上書きしないので、何回打っても大丈夫です。別のフォルダに作るときは `init ~/apps/collar` のようにフォルダを書きます。

```text
~/apps/pico-cpp/
├── CMakeLists.txt          ビルドの設定（下で説明）
├── pico_sdk_import.cmake   SDK を読み込む（SDK からコピーしたもの）
├── .gitignore              git で build フォルダを管理しないための設定
├── blink.cpp               Lチカ（最初のプログラム）
├── mpu6050.h               MPU-6050 を読むクラス（7章）
├── ws2812.h                RGB LED を光らせるクラス（4章）
└── build/                  ビルドしてできたファイル（.uf2 など）。cmake を打つとできる
```

Pico Studio の「PC に保存」も、このフォルダに保存します。初めて保存したときに、このフォルダがなければ自動で作ります。

### CMakeLists.txt

ビルドの設定です。**このフォルダの `.cpp` が、1つずつプログラムになります**（`blink.cpp` → `build/blink.uf2`）。
4〜10章の C++ のコードは、`.cpp` として保存すれば、どれもそのままビルドできます。中心の部分は次のとおりです。

```cmake
cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)        # pico_sdk_init より前に読む
project(pico_cpp C CXX ASM)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

set(PICO_LIBS pico_stdlib hardware_adc hardware_i2c ...)   # 使うライブラリ（Pico Studio と同じ）

file(GLOB APP_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_LIST_DIR}/*.cpp")
foreach(src IN LISTS APP_SOURCES)
    get_filename_component(name "${src}" NAME_WE)   # blink.cpp → blink
    add_executable(${name} "${src}")
    target_link_libraries(${name} ${PICO_LIBS})
    pico_enable_stdio_usb(${name} 1)                # printf を USB に出す
    pico_add_extra_outputs(${name})                 # .uf2 も作る
endforeach()
```

| 行 | 意味 |
| --- | --- |
| `project(pico_cpp C CXX ASM)` | プロジェクトの名前と、使う言語（C、C++、アセンブリ） |
| `pico_sdk_init()` | SDK の準備 |
| `set(PICO_LIBS ...)` | 使うライブラリ。`pico_stdlib` は GPIO・時間・`printf` などの基本、`hardware_i2c` は I2C など |
| `file(GLOB ... *.cpp)` | フォルダの `.cpp` を全部探す |
| `add_executable(blink blink.cpp)` | `blink.cpp` から `blink` というプログラムを作る |
| `pico_enable_stdio_usb(... 1)` | `printf` の出力を USB シリアルに出す。**これがないと出力が見えない** |
| `pico_add_extra_outputs` | 書き込み用の `.uf2` ファイルも作る |

- `test_` で始まる `.cpp` は、PC 用のテスト（18章）なので、ピコ用にはビルドしません
- 1つのプログラムを複数の `.cpp` に分けたいとき（15章）は、`add_executable(collar collar.cpp sensor.cpp)` のように、自分で行を書き足します

### blink.cpp

ボードの LED（GP25）を点滅させます。4章の Lチカと同じ動きです。

```cpp
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint LED_PIN = 25;

int main() {
    stdio_init_all();                  // printf を使えるようにする

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);   // 出力にする

    bool on = false;
    while (true) {
        on = !on;
        gpio_put(LED_PIN, on);
        printf("LED %s\n", on ? "ON" : "OFF");
        sleep_ms(500);
    }
}
```

MicroPython と比べると、次のようになります。

| MicroPython | C++ |
| --- | --- |
| `from machine import Pin` | `#include "pico/stdlib.h"` |
| `led = Pin(25, Pin.OUT)` | `gpio_init(25);` と `gpio_set_dir(25, GPIO_OUT);` |
| `led.value(1)` | `gpio_put(25, true);` |
| `time.sleep(0.5)` | `sleep_ms(500);` |
| `print(...)` | `printf(...);` |
| ファイルの一番上から実行される | `main()` から実行される |

- **`main()` は終わらないようにします。** パソコンと違って戻る先がないので、`while (true)` でくり返します
- Pico W では LED が無線のチップにつながっているので、GP25 では点きません。Pico W の LED は `pico_cyw43_arch` というライブラリで動かします

### ビルドする

```bash
cd ~/apps/pico-cpp
cmake -S . -B build
make -C build -j4 blink
```

- `cmake -S . -B build` は、今のフォルダ（`.`）の `CMakeLists.txt` を読んで、`build` フォルダにビルドの手順（Makefile）を作ります。**最初と、`.cpp` を足したり消したりしたとき**に打ちます
- `make -C build -j4 blink` で、`build` フォルダで `blink` だけをビルドします。`-j4` は4つ同時に進めて速くするオプションです。`blink` を省くと全部をビルドします
- 1回目は SDK 全体をビルドするので、数分かかります。2回目からは変えたところだけなので、数秒です

うまくいくと、`build/blink.uf2` ができます。

```bash
ls -l build/blink.uf2
```

> Pico 2 のときは、`cmake -S . -B build -DPICO_BOARD=pico2` のようにボードの種類を指定します（Pico W は `pico_w`、Pico 2 W は `pico2_w`）。
> 種類を変えるときは、`rm -rf build` で `build` フォルダを消してから `cmake` をやり直します。

### 書き込む

MicroPython を書き込んだときと同じで、書き込みモード（BOOTSEL）のピコに .uf2 をコピーします。

1. ピコの **BOOT** を押したまま USB をつなぐ（1章）
2. `RPI-RP2` というドライブが出てきたら、`blink.uf2` をコピーする

```bash
cp blink.uf2 /run/media/$USER/RPI-RP2/
```

コピーが終わると、ピコが自動で再起動して LED が点滅し始めます。

> ドライブの場所は PC によって違います。`/run/media/$USER/` に見つからないときは、`/media/$USER/` を見てください。

**Pico Studio で書き込むこともできます。** 書き込みモードのピコをつなぐと出る「.uf2 ファイルを選ぶ」で、`build/blink.uf2` を選びます。

#### BOOT を押さずに書き込む（picotool）

毎回 BOOT を押すのが面倒なときは、**picotool** を使います（`setup-sdk.sh` の 5/5 で `~/.local/bin/picotool` に入ります）。
`printf` を USB に出しているプログラムが動いていれば、`-f` を付けると、自動で書き込みモードにして書き込みます。

```bash
cd ~/apps/pico-cpp
picotool load -x -f build/blink.uf2
```

- MicroPython が動いているときは `-f` が効きません。先に `mpremote bootloader` で書き込みモードにしてから、`picotool load -x build/blink.uf2` を打ちます
- ビルドの途中で `build/_deps` の中にも picotool ができますが、これは `.uf2` を作るためだけのもので、USB の機能がありません（ピコの操作には使えません）

### 出力を見る

`printf` の出力は、USB シリアル（`/dev/ttyACM0`）に出ています。
Pico Studio なら、コード欄で C++ を選んで「接続」すると、出力欄に出ます。
コマンドで見るときは、pyserial に入っている **miniterm** を使います。

```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200
```

```text
--- Miniterm on /dev/ttyACM0  115200,8,N,1 ---
--- Quit: Ctrl+] | Menu: Ctrl+T | Help: Ctrl+T followed by Ctrl+H ---
LED ON
LED OFF
LED ON
```

- 止めるときは **Ctrl + ]** です（Ctrl + C ではありません）
- Pico Studio が同じポートに「接続」していると開けません。先に「切断」します
- 書き込み直すと、ピコが再起動してポートが一度消えます。miniterm は止めて、つなぎ直します

起動した直後の `printf` は、PC がポートを開く前に出てしまい、見えないことがあります。
最初の出力も見たいときは、`stdio_init_all();` のあとに次の行を入れて、PC がつなぐまで待たせます（`#include "pico/stdio_usb.h"` が必要）。

```cpp
while (!stdio_usb_connected()) sleep_ms(100);
```

> PC につながないで動かすと、ここで止まったままになります。確かめ終わったら消してください。

## MicroPython と C++ の対応表

これまでの章で使った書き方が、C++ では何にあたるかの一覧です。
`CMakeLists.txt` の列は、その機能が入っているライブラリです。Pico Studio と `cpp_build.py init` で作ったプロジェクトには、どれも最初から入っています。

| やること | MicroPython | C++（Pico SDK） | CMakeLists.txt |
| --- | --- | --- | --- |
| 出力にする | `Pin(25, Pin.OUT)` | `gpio_init(25); gpio_set_dir(25, GPIO_OUT);` | |
| 出す | `led.value(1)` | `gpio_put(25, true);` | |
| プルアップ付きの入力 | `Pin(24, Pin.IN, Pin.PULL_UP)` | `gpio_init(24); gpio_set_dir(24, GPIO_IN); gpio_pull_up(24);` | |
| 読む | `btn.value()` | `gpio_get(24)` | |
| 待つ | `time.sleep_ms(20)` | `sleep_ms(20);` | |
| 起動してからの時間 | `time.ticks_ms()` / `ticks_us()` | `to_ms_since_boot(get_absolute_time())` / `time_us_64()` | |
| アナログ入力 | `ADC(26).read_u16()`（0〜65535） | `adc_gpio_init(26); adc_select_input(0); adc_read()`（0〜4095） | `hardware_adc` |
| I2C の準備 | `I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)` | `i2c_init(i2c0, 400000);` と `gpio_set_function(4, GPIO_FUNC_I2C);` など | `hardware_i2c` |
| レジスタを読む | `i2c.readfrom_mem(addr, reg, n)` | `i2c_write_blocking(...)` で番号を送ってから `i2c_read_blocking(...)` | `hardware_i2c` |
| レジスタに書く | `i2c.writeto_mem(addr, reg, b"\x00")` | `i2c_write_blocking(...)` で番号と値を続けて送る | `hardware_i2c` |
| PWM | `PWM(Pin(15))` | `gpio_set_function(15, GPIO_FUNC_PWM);` と `pwm_set_wrap` など | `hardware_pwm` |
| 2バイトを数にする | `struct.unpack(">h", d)` | `int16_t v = (d[0] << 8) + d[1];` | |
| タイマー割り込み | `machine.Timer` | `add_repeating_timer_ms(...)` | |
| 2つ目のコア | `_thread` | `multicore_launch_core1(...)` | `pico_multicore` |
| ウォッチドッグ | `machine.WDT(timeout=2000)` | `watchdog_enable(2000, true);` と `watchdog_update();` | `hardware_watchdog` |
| ファイルに保存 | `open("log.csv", "a")` | なし。USB で PC に送る | |

- ADC の値の範囲が違います。MicroPython の `read_u16()` は 0〜65535 に広げた値、C++ の `adc_read()` はそのままの 12 ビット（0〜4095）です
- ADC の番号は、GP26 が 0、GP27 が 1、GP28 が 2、内蔵温度センサーが 4 です

## mpu6050.h の全体

7章で使う MPU-6050 のクラスです。Pico Studio には最初から入っています（`cpp/include/mpu6050.h`）。
コマンドでビルドするときは、プロジェクトのフォルダに次の内容で `mpu6050.h` を作ります。

```cpp
#pragma once
#include <cstdint>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

class Mpu6050 {
public:
    explicit Mpu6050(i2c_inst_t* i2c, uint8_t addr = 0x68) : i2c_(i2c), addr_(addr) {}

    // ピンを設定して、センサーを起こす。成功すれば true
    bool begin(uint sda, uint scl, uint baud = 400 * 1000) {
        i2c_init(i2c_, baud);
        gpio_set_function(sda, GPIO_FUNC_I2C);
        gpio_set_function(scl, GPIO_FUNC_I2C);
        gpio_pull_up(sda);
        gpio_pull_up(scl);

        bool ok = write_reg(0x6B, 0x00)      // スリープ解除
               && write_reg(0x1C, 0x00)      // 加速度 ±2g     → 16384 = 1g
               && write_reg(0x1B, 0x00);     // ジャイロ ±250°/s → 131 = 1°/s
        sleep_ms(100);
        return ok;
    }

    uint8_t who_am_i() {
        uint8_t v = 0;
        read_regs(0x75, &v, 1);
        return v;
    }

    // 加速度 [g] だけを読む（6バイト）
    bool read_accel(float& ax, float& ay, float& az) {
        uint8_t d[6];
        if (!read_regs(0x3B, d, 6)) return false;
        ax = to_i16(d[0], d[1]) / 16384.0f;
        ay = to_i16(d[2], d[3]) / 16384.0f;
        az = to_i16(d[4], d[5]) / 16384.0f;
        return true;
    }

    // 加速度 [g]・角速度 [°/s]・温度 [℃] をまとめて読む（14バイト）
    bool read_all(float acc[3], float gyro[3], float& temp) {
        uint8_t d[14];
        if (!read_regs(0x3B, d, 14)) return false;
        for (int i = 0; i < 3; i++) {
            acc[i] = to_i16(d[i * 2], d[i * 2 + 1]) / 16384.0f;
            gyro[i] = to_i16(d[8 + i * 2], d[9 + i * 2]) / 131.0f;
        }
        temp = to_i16(d[6], d[7]) / 340.0f + 36.53f;
        return true;
    }

private:
    // ビッグエンディアンの2バイトを、符号付き16ビットの数にする（struct.unpack(">h") と同じ）
    static int16_t to_i16(uint8_t hi, uint8_t lo) {
        return static_cast<int16_t>((hi << 8) | lo);
    }

    // writeto_mem と同じ。レジスタの番号と値を続けて送る
    bool write_reg(uint8_t reg, uint8_t value) {
        uint8_t buf[2] = {reg, value};
        return i2c_write_blocking(i2c_, addr_, buf, 2, false) == 2;
    }

    // readfrom_mem と同じ。番号を送ってから、続けて len バイト読む
    bool read_regs(uint8_t reg, uint8_t* dst, size_t len) {
        if (i2c_write_blocking(i2c_, addr_, &reg, 1, true) != 1) return false;   // true = 通信を切らずに続ける
        return i2c_read_blocking(i2c_, addr_, dst, len, false) == static_cast<int>(len);
    }

    i2c_inst_t* i2c_;
    uint8_t addr_;
};
```

| コード | 意味 |
| --- | --- |
| `i2c_inst_t* i2c_` | どの I2C を使うか。`i2c0` か `i2c1`。GP4・GP5 は `i2c0` |
| `gpio_set_function(sda, GPIO_FUNC_I2C)` | そのピンを I2C 用に切り替える。MicroPython の `sda=Pin(4)` にあたる |
| `i2c_write_blocking(..., true)` | 最後の `true` は「通信を切らずに、続けて読む」。レジスタを読むときの決まった手順 |
| 戻り値 `== 2` など | 送れた・読めたバイト数。つながっていないと負の数（エラー）が返る |
| `static_cast<int16_t>(...)` | 0〜65535 の数を、−32768〜32767 として読み直す |

MicroPython では、エラーのときに `OSError` が出てプログラムが止まりました。
C++ の SDK は止まらずに**負の数を返す**だけなので、戻り値を確かめるようにしています。

## プログラムを足す

4〜10章のコードを足すときは、`~/apps/pico-cpp` に `.cpp` として保存して（Pico Studio の「PC に保存」でもよい）、`cmake` を打ち直します。

```bash
cd ~/apps/pico-cpp
cmake -S . -B build
make -C build -j4 temp
```

使えるライブラリは Pico Studio と同じです（この章の「Pico Studio のビルドのしくみ」の表）。ここにないもの（Pico W の無線で TCP/IP を使う `pico_cyw43_arch_lwip_threadsafe_background` など）を使うときは、`CMakeLists.txt` の `set(PICO_LIBS ...)` に足します。

### 手順をスクリプトにする

ビルドから書き込みまでを、1つのスクリプトにまとめておくと楽です。次の内容を `~/apps/pico-cpp/flash.sh` として保存します。

```bash
#!/bin/sh
# 使い方: sh flash.sh blink   （先にピコを書き込みモードにしておく）
set -e
cd "$(dirname "$0")"
make -C build -j4 "$1"
cp "build/$1.uf2" /run/media/$USER/RPI-RP2/
echo "$1.uf2 を書き込みました"
```

```bash
sh flash.sh blink
```

## MicroPython に戻す

C++ のプログラムを書き込んだあとで、また MicroPython と Pico Studio を使いたいときは、MicroPython を書き込み直します。

1. Pico Studio のコード欄で **Python** を選ぶ
2. ピコの **BOOT** を押したまま USB をつなぐ
3. 「最新の MicroPython を書き込む」を押す（0章）
4. 「更新」を押してから接続する

- ピコに保存していたファイル（`main.py` など）は、残っていることが多いですが、**消えることもあります**。大事なファイルは、C++ を書き込む前に PC にコピーしておきます（2章の `mpremote cp`）
- 全部を消して最初からにしたいときは、11章の flash_nuke.uf2 を使います

## 困ったとき

| 症状 | 原因と直し方 |
| --- | --- |
| `cd: /home/…/pico-cpp: そのようなファイルやディレクトリはありません` | プロジェクトのフォルダがまだない。`python3 ~/apps/pico-studio/cpp_build.py init` |
| `SDK location was not specified. Please set PICO_SDK_PATH` | `PICO_SDK_PATH` が設定されていない。スクリプトの前から開いていたターミナルでは効いていないので、`source ~/.bashrc` を打つか開き直す。`cpp_build.py init` で作った `CMakeLists.txt` は `~/pico/pico-sdk` を自分で探すので、`python3 ~/apps/pico-studio/cpp_build.py init` で新しい形にしてもよい |
| `does not appear to contain CMakeLists.txt` | `CMakeLists.txt` がないフォルダで `cmake` を打った。`cd ~/apps/pico-cpp` してから打つ |
| `cmake` で `PICO_SDK_PATH` が見つからないと出る | 「SDK の場所を登録する」をしていない。ターミナルを開き直したか確かめる。`python3 ~/apps/pico-studio/cpp_build.py check` で足りないものがわかる |
| `arm-none-eabi-gcc` が見つからないと出る | `gcc-arm-none-eabi` を入れていない |
| `fatal error: hardware/i2c.h: No such file or directory` | 自分で書いた `CMakeLists.txt` に `hardware_i2c` を足していない（ADC なら `hardware_adc`） |
| `undefined reference to 'multicore_launch_core1'` | `pico_multicore` を足していない |
| `printf` の出力が出ない | `pico_enable_stdio_usb(... 1)` があるか。`git submodule update --init` をしたか。Pico Studio が同じポートに接続していないか |
| 最初の数行だけ出ない | PC がつなぐ前に出ている。「出力を見る」の `stdio_usb_connected()` を使う |
| `/dev/ttyACM0` が出てこない | `pico_enable_stdio_usb` がないと、USB シリアルのポート自体ができない |
| Pico W で LED が点かない | Pico W の LED は GP25 ではない。`pico_cyw43_arch` を使う |
| Pico 2 で動かない | `cmake -DPICO_BOARD=pico2 ..` でビルドし直す（`build` フォルダを消してから） |
| ビルドの途中で picotool のダウンロードに失敗する | `libusb-1.0-0-dev` と `pkg-config` を入れて、もう一度 `cmake -S . -B build` する |
| I2C の読み取りが失敗する | 7章・11章と同じように配線とアドレスを確かめる。I2C スキャン（6章）で見つかるかを先に確かめると早い |
| Pico Studio の「C++ の開発環境」が赤い | 足りないものが表示される。SDK を `~/pico/pico-sdk` 以外に置いたときは、`PICO_SDK_PATH` を設定してから Pico Studio を起動し直す |
| Pico Studio で書き込みモードにならない | 前のプログラムが `stdio_init_all()` を呼んでいないか、止まっている。BOOT を押しながら USB をつなぎ直して、もう一度押す |

## まとめ

- C++ は、PC でビルドして .uf2 を書き込む。速くて製品向きだが、すぐ試すことはできない
- 開発環境は `gcc-arm-none-eabi` と Pico SDK。SDK は `~/pico/pico-sdk` に置くか、`PICO_SDK_PATH` で教える
- Pico Studio では「C++」を選んで「▶ ビルドして書き込む」。書き込みモードへの切り替えも自動
- 自分でプロジェクトを作るときは、`CMakeLists.txt` にプログラムと使うライブラリを書き、`cmake` → `make` でビルドする
- `Pin` は `gpio_init` / `gpio_put`、`readfrom_mem` は `i2c_write_blocking` + `i2c_read_blocking`、`ticks_add` は `delayed_by_ms` + `sleep_until`
- 試すのは MicroPython、製品にするのは C++、と使い分ける
