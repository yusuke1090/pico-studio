# 14. C++ で実装する

## この章でわかること

- MicroPython と C++ の進め方の違い
- PC に C++ の開発環境（Pico SDK）を用意する手順
- ビルドして .uf2 を作り、ピコに書き込む手順
- MicroPython の書き方と C++ の書き方の対応
- これまでの章のプログラム（Lチカ・ボタン・温度・MPU-6050・一定間隔の測定・決定木の判定）を C++ で書く方法
- 2つのコアを使う方法と、MicroPython に戻す方法

C++ の文法の基本（変数・関数・クラス）がわかる前提で書いています。
ここでは Raspberry Pi 公式の **Pico SDK** を使います。

## MicroPython との違い

| 項目 | MicroPython | C++（Pico SDK） |
| --- | --- | --- |
| 動かすまで | コードを送れば、すぐ動く | PC でビルドして、.uf2 を書き込む |
| 速さ | 遅い | 10〜100 倍速い |
| ピコに入っているもの | MicroPython と、自分の .py ファイル | 自分のプログラムだけ（.uf2 にまとまっている） |
| 対話で試す（REPL） | できる | できない |
| ファイルの保存 | `open()` でピコに保存できる | ファイルのしくみがない。PC に送って保存する |
| `print` の出力 | Pico Studio の出力欄 | シリアルモニター（この章の「出力を見る」） |
| Pico Studio | 使える | .uf2 の書き込みだけ使える |
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

### 1. コンパイラなどを入れる

```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib build-essential git python3 libusb-1.0-0-dev pkg-config
```

| パッケージ | 役割 |
| --- | --- |
| `cmake` | ビルドの手順を作るソフト |
| `gcc-arm-none-eabi` | ピコ（ARM）用のコンパイラ。PC の `g++` ではピコのプログラムは作れない |
| `libnewlib-arm-none-eabi`、`libstdc++-arm-none-eabi-newlib` | ピコ用の C / C++ の標準ライブラリ |
| `build-essential` | `make` など |
| `libusb-1.0-0-dev`、`pkg-config` | ビルドのときに picotool（ピコを操作するツール）を自動で作るのに使う |

### 2. Pico SDK をダウンロードする

```bash
mkdir -p ~/pico
cd ~/pico
git clone --branch 2.1.1 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
```

- `--branch 2.1.1` はバージョンの指定です。新しいバージョンは [リリースのページ](https://github.com/raspberrypi/pico-sdk/releases) で確かめられます
- `git submodule update --init` は、SDK が使う USB のライブラリ（TinyUSB）などをダウンロードします。**これを忘れると、USB で `printf` が出ません**

### 3. SDK の場所を登録する

ビルドのときに SDK の場所がわかるように、`~/.bashrc` に書いておきます。

```bash
echo 'export PICO_SDK_PATH=~/pico/pico-sdk' >> ~/.bashrc
source ~/.bashrc
```

> VS Code を使っているなら、拡張機能の **Raspberry Pi Pico** を入れると、ここまでの準備とビルド・書き込みをボタンでできます。
> この章では、何が起きているかわかるように、コマンドで進めます。

## 最初のプログラム（Lチカ）

### フォルダを作る

この章のプログラムは、全部1つのフォルダ（プロジェクト）にまとめます。

```bash
mkdir -p ~/apps/pico-cpp
cd ~/apps/pico-cpp
cp $PICO_SDK_PATH/external/pico_sdk_import.cmake .
```

`pico_sdk_import.cmake` は、プロジェクトから SDK を読み込むためのファイルです。SDK に入っているものをコピーして使います。

最後は、次の形になります。

```text
~/apps/pico-cpp/
├── CMakeLists.txt          ビルドの設定
├── pico_sdk_import.cmake   SDK を読み込む（コピーしたもの）
├── blink.cpp               Lチカ
├── button.cpp              ボタン
├── temp.cpp                内蔵温度センサー
├── mpu6050.h               MPU-6050 を読むクラス
├── mpu.cpp                 MPU-6050 の読み取り
├── sampling.cpp            一定間隔の測定（PC に送る）
├── model.h                 決定木（train.py で作る）
├── judge.cpp               決定木で判定する
├── multicore.cpp           2つのコアを使う
└── build/                  ビルドしてできたファイル（.uf2 など）
```

### CMakeLists.txt

ビルドの設定です。次の内容で `CMakeLists.txt` を作ります。

```cmake
cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)        # pico_sdk_init より前に読む

project(pico_cpp C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# プログラムを1つ追加する関数。pico_app(名前 使うライブラリ...)
function(pico_app name)
    add_executable(${name} ${name}.cpp)
    target_link_libraries(${name} pico_stdlib ${ARGN})
    pico_enable_stdio_usb(${name} 1)     # printf を USB に出す
    pico_enable_stdio_uart(${name} 0)    # UART（GP0, GP1）には出さない
    pico_add_extra_outputs(${name})      # .uf2 も作る
endfunction()

pico_app(blink)
```

| 行 | 意味 |
| --- | --- |
| `project(pico_cpp C CXX ASM)` | プロジェクトの名前と、使う言語（C、C++、アセンブリ） |
| `pico_sdk_init()` | SDK の準備 |
| `add_executable(blink blink.cpp)` | `blink.cpp` から `blink` というプログラムを作る |
| `target_link_libraries(... pico_stdlib)` | 使うライブラリ。`pico_stdlib` は GPIO・時間・`printf` などの基本 |
| `pico_enable_stdio_usb(... 1)` | `printf` の出力を USB シリアルに出す。**これがないと出力が見えない** |
| `pico_add_extra_outputs` | 書き込み用の `.uf2` ファイルも作る |

このあとプログラムを足すときは、最後に `pico_app(...)` の行を足していきます。

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
mkdir -p build
cd build
cmake ..
make -j4 blink
```

- `cmake ..` は、1つ上のフォルダの `CMakeLists.txt` を読んで、ビルドの手順（Makefile）を作ります。`CMakeLists.txt` を変えたとき以外は、2回目からは要りません
- `make -j4 blink` で `blink` だけをビルドします。`-j4` は4つ同時に進めて速くするオプションです。`make -j4` だけなら全部をビルドします
- 1回目は SDK 全体をビルドするので、数分かかります。2回目からは変えたところだけなので、数秒です

うまくいくと、`build` フォルダに `blink.uf2` ができます。

```bash
ls -l blink.uf2
```

> Pico 2 のときは、`cmake -DPICO_BOARD=pico2 ..` のようにボードの種類を指定します（Pico W は `pico_w`、Pico 2 W は `pico2_w`）。
> 種類を変えるときは、`build` フォルダを消してから `cmake` をやり直します。

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

毎回 BOOT を押すのが面倒なときは、ビルドのときに一緒にできた **picotool** を使います。
`printf` を USB に出しているプログラムが動いていれば、`-f` を付けると、自動で書き込みモードにして書き込みます。

```bash
cd ~/apps/pico-cpp
sudo build/_deps/picotool/picotool load -x -f build/blink.uf2
```

- picotool の場所は、PC によって変わることがあります。見つからないときは `find ~/apps/pico-cpp/build -name picotool -type f` で探します
- `sudo` なしで使うには、[picotool の udev ルール](https://github.com/raspberrypi/picotool/blob/master/udev/60-picotool.rules) を入れます

### 出力を見る

`printf` の出力は、USB シリアル（`/dev/ttyACM0`）に出ています。
Pico Studio は MicroPython 用なので、ここでは使えません（「接続」すると「MicroPython の応答がありません」と出ます）。
代わりに、pyserial に入っている **miniterm** で見ます。

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
`CMakeLists.txt` の列は、`pico_app(...)` に足すライブラリです（`pico_stdlib` は最初から入っています）。

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

## ボタン（USR）

USR ボタン（GP24）を押している間、LED を点けます。4章のボタンと同じ動きです。

```cpp
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint LED_PIN = 25;
constexpr uint BTN_PIN = 24;

int main() {
    stdio_init_all();

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    gpio_init(BTN_PIN);
    gpio_set_dir(BTN_PIN, GPIO_IN);
    gpio_pull_up(BTN_PIN);             // 押していないときは 1 になる

    bool last = false;
    while (true) {
        bool pressed = !gpio_get(BTN_PIN);   // 押すと 0 なので、反対にする
        gpio_put(LED_PIN, pressed);
        if (pressed != last) {
            printf(pressed ? "押されている\n" : "離された\n");
            last = pressed;
        }
        sleep_ms(10);
    }
}
```

`CMakeLists.txt` の最後に、次の行を足します。

```cmake
pico_app(button)
```

ビルドして書き込む手順は、Lチカと同じです（`make -j4 button` → `button.uf2` を書き込む）。

## 内蔵温度センサー（ADC）

```cpp
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/adc.h"

int main() {
    stdio_init_all();

    adc_init();
    adc_set_temp_sensor_enabled(true);   // 内蔵温度センサーを使う
    adc_select_input(4);                 // 4番 = 内蔵温度センサー

    while (true) {
        uint16_t raw = adc_read();                   // 0〜4095
        float volt = raw * 3.3f / 4096;
        float temp = 27.0f - (volt - 0.706f) / 0.001721f;   // データシートの式
        printf("raw=%4u  %.3f V  %.1f C\n", raw, volt, temp);
        sleep_ms(1000);
    }
}
```

```cmake
pico_app(temp hardware_adc)
```

- `hardware_adc` を足すのを忘れると、ビルドのときに `hardware/adc.h: No such file or directory` と出ます
- `3.3f` の `f` は、`float` の数という意味です。`f` がないと `double` になり、ピコでは計算が遅くなります（ピコの CPU には小数の計算をする回路がないため）

## MPU-6050（I2C）

7章の MPU-6050 を C++ で読みます。配線は6章と同じ（SDA = GP4、SCL = GP5）です。
このあとの例でも使うので、読み取りの部分を **クラス** にして、`mpu6050.h` に分けます。

### mpu6050.h

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

### mpu.cpp

7章と同じように、0.2秒ごとに表示します。

```cpp
#include <cstdio>
#include "pico/stdlib.h"
#include "mpu6050.h"

Mpu6050 mpu(i2c0);

int main() {
    stdio_init_all();
    sleep_ms(2000);                   // PC が miniterm でつなぐのを待つ

    if (!mpu.begin(4, 5)) {
        printf("MPU-6050 が見つかりません。配線を確かめてください\n");
    }
    printf("WHO_AM_I: 0x%02x\n", mpu.who_am_i());

    while (true) {
        float acc[3], gyro[3], temp;
        if (mpu.read_all(acc, gyro, temp)) {
            printf("加速度[g] x=%+.2f y=%+.2f z=%+.2f  角速度[deg/s] x=%+6.1f y=%+6.1f z=%+6.1f\n",
                   acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2]);
        } else {
            printf("読み取りに失敗しました\n");
        }
        sleep_ms(200);
    }
}
```

```cmake
pico_app(mpu hardware_i2c)
```

机に置いたまま動かすと、7章と同じように z が 1g 前後になります。

```text
WHO_AM_I: 0x68
加速度[g] x=+0.02 y=-0.01 z=+1.01  角速度[deg/s] x=  -1.2 y=  +0.8 z=  +0.3
```

## 決まった間隔で測って PC に送る

7章の「決まった間隔でデータを取る」と、9章の「USB で PC に送る」を合わせたものです。
C++ では、**次に測る時刻**を `delayed_by_ms` で決めて、`sleep_until` でその時刻まで待ちます。

```cpp
#include <cstdio>
#include "pico/stdlib.h"
#include "mpu6050.h"

constexpr int HZ = 50;                 // 1秒に50回
constexpr int INTERVAL_MS = 1000 / HZ; // 20ms ごと

Mpu6050 mpu(i2c0);

int main() {
    stdio_init_all();
    mpu.begin(4, 5);

    absolute_time_t start = get_absolute_time();
    absolute_time_t next = start;
    while (true) {
        float ax, ay, az;
        if (mpu.read_accel(ax, ay, az)) {
            int ms = static_cast<int>(absolute_time_diff_us(start, get_absolute_time()) / 1000);
            printf("%d,%.3f,%.3f,%.3f\n", ms, ax, ay, az);
        }
        next = delayed_by_ms(next, INTERVAL_MS);   // 次に測る時刻
        sleep_until(next);                         // その時刻まで待つ
    }
}
```

```cmake
pico_app(sampling hardware_i2c)
```

- 出力の形は9章のピコ側と同じ（`ms,ax,ay,az`）なので、**9章の `pc_logger.py` で、そのまま PC に保存できます**
- `sleep_until` は、読み取りや `printf` にかかった時間を差し引いて待つので、間隔がずれません。MicroPython の `ticks_add` と `ticks_diff` を使った書き方と同じ考え方です
- C++ なら `HZ` を 200〜500 にしても間に合います（MicroPython では、`print` を毎回すると 50Hz でも遅れることがあります）
- もっと正確にしたいときは、`add_repeating_timer_us` でタイマー割り込みを使います

## 決定木を C++ で動かす

10章で学習した決定木を、C++ で動かします。
PC で学習するところは10章と同じで、**書き出す形だけ C++ にします**。

### 1. train.py に C++ の書き出しを足す

10章の `train.py` の最後に、次のコードを足します。`model.py` と一緒に `model.h` もできるようになります。

```python
def export_cpp(clf, names):
    """決定木を C++ の if 文に変換する"""
    t = clf.tree_
    lines = ["// train.py で自動生成した決定木", "#pragma once", "",
             "inline const char* predict(const float* f) {"]

    def walk(node, depth):
        pad = "    " * depth
        if t.feature[node] >= 0:                      # 分岐のノード
            i = t.feature[node]
            lines.append(f"{pad}if (f[{i}] <= {t.threshold[node]:.6f}f) {{  // {names[i]}")
            walk(t.children_left[node], depth + 1)
            lines.append(f"{pad}}} else {{")
            walk(t.children_right[node], depth + 1)
            lines.append(f"{pad}}}")
        else:                                         # 葉（判定結果）
            label = clf.classes_[t.value[node][0].argmax()]
            lines.append(f'{pad}return "{label}";')

    walk(0, 1)
    lines.append("}")
    return "\n".join(lines) + "\n"


with open("model.h", "w") as f:
    f.write(export_cpp(clf, NAMES))
print("model.h を作りました")
```

`python3 train.py` を実行すると、次のような `model.h` ができます（中身は学習したデータで変わります）。

```text
// train.py で自動生成した決定木
#pragma once

inline const char* predict(const float* f) {
    if (f[6] <= 0.041200f) {  // std_mag
        return "rest";
    } else {
        if (f[7] <= 0.183000f) {  // diff_mag
            return "walk";
        } else {
            return "run";
        }
    }
}
```

できた `model.h` を `~/apps/pico-cpp/` にコピーします。

### 2. judge.cpp

10章の「ステップ3: ピコで判定する」と同じ動きです。2秒分（25Hz × 50回）を集めて、特徴量を計算し、判定します。

```cpp
#include <cmath>
#include <cstdio>
#include "pico/stdlib.h"
#include "mpu6050.h"
#include "model.h"

constexpr int HZ = 25;
constexpr int N = HZ * 2;              // 2秒分

Mpu6050 mpu(i2c0);
float xs[N], ys[N], zs[N];             // 集めたデータ（大きさを決めておく）

// 2秒分を、決まった間隔で集める
void window() {
    absolute_time_t next = get_absolute_time();
    for (int i = 0; i < N; i++) {
        mpu.read_accel(xs[i], ys[i], zs[i]);
        next = delayed_by_ms(next, 1000 / HZ);
        sleep_until(next);
    }
}

float mean(const float* a) {
    float s = 0;
    for (int i = 0; i < N; i++) s += a[i];
    return s / N;
}

float stdev(const float* a, float m) {
    float s = 0;
    for (int i = 0; i < N; i++) s += (a[i] - m) * (a[i] - m);
    return sqrtf(s / N);
}

// 10章の features() と同じ計算。順番も同じにする
void features(float fe[8]) {
    float mag[N];
    for (int i = 0; i < N; i++) mag[i] = sqrtf(xs[i] * xs[i] + ys[i] * ys[i] + zs[i] * zs[i]);

    float mx = mean(xs), my = mean(ys), mz = mean(zs), mm = mean(mag);
    float diff = 0;
    for (int i = 1; i < N; i++) diff += fabsf(mag[i] - mag[i - 1]);

    fe[0] = mx;  fe[1] = my;  fe[2] = mz;
    fe[3] = stdev(xs, mx);  fe[4] = stdev(ys, my);  fe[5] = stdev(zs, mz);
    fe[6] = stdev(mag, mm);
    fe[7] = diff / (N - 1);
}

int main() {
    stdio_init_all();
    mpu.begin(4, 5);

    while (true) {
        window();
        float fe[8];
        features(fe);

        uint64_t t0 = time_us_64();
        const char* label = predict(fe);
        unsigned us = static_cast<unsigned>(time_us_64() - t0);
        printf("判定: %s  （判定にかかった時間 %u us）\n", label, us);
    }
}
```

```cmake
pico_app(judge hardware_i2c)
```

2秒ごとに判定結果が出ます（数値は例です）。

```text
判定: rest  （判定にかかった時間 2 us）
判定: walk  （判定にかかった時間 2 us）
```

- 判定にかかる時間は、MicroPython より大幅に短くなります
- `features()` は、**10章のデータを集めたときと同じ計算**にします。`std` は「N で割る」ほう（numpy の標準と同じ）です
- `xs` などは、関数の外で大きさを決めて作っています。MicroPython のように `append` で増やすより、メモリの使い方がわかりやすく、途中でメモリが足りなくなることもありません

## 2つのコアを使う

ピコのチップにはコアが2つあります。MicroPython の `_thread` は実験的な機能でしたが、C++ では普通に使えます。
次の例では、コア1が LED を点滅させ、コア0（`main` が動くほう）が温度を測ります。

```cpp
#include <cstdio>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/adc.h"

constexpr uint LED_PIN = 25;

// コア1で動く関数。終わらないようにする
void core1_main() {
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    bool on = false;
    while (true) {
        on = !on;
        gpio_put(LED_PIN, on);
        sleep_ms(250);
    }
}

int main() {
    stdio_init_all();
    multicore_launch_core1(core1_main);   // コア1で動かし始める

    adc_init();
    adc_set_temp_sensor_enabled(true);
    adc_select_input(4);

    while (true) {
        float volt = adc_read() * 3.3f / 4096;
        printf("温度 %.1f C\n", 27.0f - (volt - 0.706f) / 0.001721f);
        sleep_ms(1000);
    }
}
```

```cmake
pico_app(multicore pico_multicore hardware_adc)
```

- それぞれのコアが自分の `while` を回すので、片方が待っていても、もう片方は止まりません
- 2つのコアで同じ変数を使うときは、同時に書き換えないように注意します。数値を渡すだけなら `multicore_fifo_push_blocking` と `multicore_fifo_pop_blocking` が簡単です
- 1つのコアの中で複数の処理を交代で動かすなら、12章の `asyncio` と同じように、時刻を見て順に処理する書き方にします

## 全部をビルドする

ここまでの `pico_app(...)` を全部足した `CMakeLists.txt` の最後の部分です。

```cmake
pico_app(blink)
pico_app(button)
pico_app(temp hardware_adc)
pico_app(mpu hardware_i2c)
pico_app(sampling hardware_i2c)
pico_app(judge hardware_i2c)
pico_app(multicore pico_multicore hardware_adc)
```

`CMakeLists.txt` を変えたら、`build` フォルダで `cmake ..` をやり直してから `make` します。

```bash
cd ~/apps/pico-cpp/build
cmake ..
make -j4
```

`build` フォルダに、プログラムごとの .uf2 ができます。書き込めるのは1つだけなので、使いたいものを選んで書き込みます。

### 手順をスクリプトにする

ビルドから書き込みまでを、1つのスクリプトにまとめておくと楽です。次の内容を `~/apps/pico-cpp/flash.sh` として保存します。

```bash
#!/bin/sh
# 使い方: sh flash.sh blink   （先にピコを書き込みモードにしておく）
set -e
cd "$(dirname "$0")/build"
make -j4 "$1"
cp "$1.uf2" /run/media/$USER/RPI-RP2/
echo "$1.uf2 を書き込みました"
```

```bash
sh flash.sh blink
```

## MicroPython に戻す

C++ のプログラムを書き込んだあとで、また MicroPython と Pico Studio を使いたいときは、MicroPython を書き込み直します。

1. ピコの **BOOT** を押したまま USB をつなぐ
2. Pico Studio の「最新の MicroPython を書き込む」を押す（0章）
3. 「更新」を押してから接続する

- ピコに保存していたファイル（`main.py` など）は、残っていることが多いですが、**消えることもあります**。大事なファイルは、C++ を書き込む前に PC にコピーしておきます（2章の `mpremote cp`）
- 全部を消して最初からにしたいときは、11章の flash_nuke.uf2 を使います

## 困ったとき

| 症状 | 原因と直し方 |
| --- | --- |
| `cmake ..` で `PICO_SDK_PATH` が見つからないと出る | 「SDK の場所を登録する」をしていない。ターミナルを開き直したか確かめる |
| `arm-none-eabi-gcc` が見つからないと出る | `gcc-arm-none-eabi` を入れていない |
| `fatal error: hardware/i2c.h: No such file or directory` | `pico_app(...)` に `hardware_i2c` を足していない（ADC なら `hardware_adc`） |
| `undefined reference to 'multicore_launch_core1'` | `pico_multicore` を足していない |
| `printf` の出力が出ない | `pico_enable_stdio_usb(... 1)` があるか。`git submodule update --init` をしたか。Pico Studio が同じポートに接続していないか |
| 最初の数行だけ出ない | PC がつなぐ前に出ている。「出力を見る」の `stdio_usb_connected()` を使う |
| `/dev/ttyACM0` が出てこない | `pico_enable_stdio_usb` がないと、USB シリアルのポート自体ができない |
| Pico W で LED が点かない | Pico W の LED は GP25 ではない。`pico_cyw43_arch` を使う |
| Pico 2 で動かない | `cmake -DPICO_BOARD=pico2 ..` でビルドし直す（`build` フォルダを消してから） |
| ビルドの途中で picotool のダウンロードに失敗する | `libusb-1.0-0-dev` と `pkg-config` を入れて、もう一度 `cmake ..` する |
| I2C の読み取りが失敗する | 7章・11章と同じように配線とアドレスを確かめる。MicroPython の I2C スキャン（6章）で見つかるかを先に確かめると早い |

## まとめ

- C++ は、PC でビルドして .uf2 を書き込む。速いが、すぐ試すことはできない
- 開発環境は `gcc-arm-none-eabi` と Pico SDK。SDK の場所は `PICO_SDK_PATH` で教える
- `CMakeLists.txt` にプログラムと使うライブラリ（`hardware_i2c` など）を書き、`cmake ..` → `make` でビルドする
- 書き込みは BOOTSEL のピコに .uf2 をコピーする。Pico Studio の「.uf2 ファイルを選ぶ」でもできる
- 出力は miniterm で見る。Pico Studio の「接続」は MicroPython 用
- `Pin` は `gpio_init` / `gpio_put`、`readfrom_mem` は `i2c_write_blocking` + `i2c_read_blocking`、`ticks_add` は `delayed_by_ms` + `sleep_until`
- 決定木は `train.py` から `model.h` を書き出せば、そのまま C++ で使える
- 試すのは MicroPython、決まった処理を速く・長く動かすのは C++、と使い分ける
