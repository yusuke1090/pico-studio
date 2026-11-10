# 15. マイコン向けの C++ の書き方

## この章でわかること

- マイコンで C++ を書くときに、パソコンと違うところ
- 整数と小数の型の選び方
- メモリの置き場所と、`new` を使わない書き方
- 使ってよい標準ライブラリと、避けるもの
- エラーの扱い方（例外を使わない）
- クラスでセンサーを扱う書き方と、ファイルの分け方
- 「待たない」書き方（状態機械）で、いくつもの動きを同時に進める

14章の開発環境ができている前提です。この章のコードは、Pico Studio で C++ を選んで「▶ ビルドして書き込む」で試せます。

## パソコンの C++ との違い

| 項目 | パソコン | ピコ |
| --- | --- | --- |
| メモリ | 数GB | 264KB（Pico 2 は 520KB） |
| 小数の計算 | 速い | 遅い（Pico は小数の計算回路がない。Pico 2 は `float` だけ速い） |
| 例外（`try` / `throw`） | 使う | Pico SDK では使わない設定になっている |
| 標準ライブラリ | 全部使える | 一部だけ。`std::cout` や `std::thread` は使わない |
| プログラムの終わり | `main` が終わると終わる | `main` は終わらない。ずっとくり返す |
| エラーで止まったとき | OS が知らせてくれる | 何も出ずに止まる。自分で気付けるようにする（17章のウォッチドッグ） |

## 整数の型

ピコの C++ では、**大きさが決まった型**を使います。`int` の大きさは環境によって違うことがあるためです。

| 型 | 大きさ | 範囲 | 使い道 |
| --- | --- | --- | --- |
| `uint8_t` | 1バイト | 0〜255 | I2C のデータ、バイト列 |
| `int16_t` | 2バイト | −32768〜32767 | センサーの生の値（MPU-6050 など） |
| `uint16_t` | 2バイト | 0〜65535 | ADC の値 |
| `int32_t` / `uint32_t` | 4バイト | 約 ±21億 / 0〜約43億 | 時刻（ミリ秒）、計算の途中 |
| `uint64_t` | 8バイト | とても大きい | 時刻（マイクロ秒、`time_us_64()`） |
| `uint` | 4バイト | 0〜約43億 | Pico SDK のピン番号など |
| `size_t` | 4バイト | 0〜約43億 | 配列の大きさ |

```cpp
uint8_t hi = 200, lo = 100;
int16_t raw = static_cast<int16_t>((hi << 8) | lo);   // 2バイトをつなげる（7章）
uint32_t ms = to_ms_since_boot(get_absolute_time());  // 起動してからのミリ秒。約49日で一周する
```

- 掛け算の途中で範囲を超えると、おかしな値になります（オーバーフロー）。`int16_t` どうしの計算でも、途中は `int32_t` で行います
- ミリ秒の `uint32_t` は約49日で 0 に戻ります。長く動かす製品では、時刻の差を `int32_t` で計算するか、`uint64_t` のマイクロ秒を使います

## 小数の型

| 型 | 速さ（Pico） | 精度 |
| --- | --- | --- |
| `float` | 遅め（ソフトで計算。1回 1マイクロ秒前後） | 7けたくらい |
| `double` | もっと遅い（`float` の2〜3倍） | 15けたくらい |
| 整数 | 速い | 小数はない |

- 小数は **`float`** を使い、数には **`f`** を付けます（`3.3f`）。`f` がないと `double` になります
- 関数も `float` 用を使います（`sqrtf`、`fabsf`、`powf`）
- たくさん計算するところは、**単位を小さくして整数で計算**すると速くなります

```cpp
// 小数: 0.981 g
float az = raw / 16384.0f;

// 整数: 981 mg（ミリ g）。小数を使わずに同じ意味を表せる
int32_t az_mg = raw * 1000 / 16384;
```

> Pico 2（RP2350）は `float` の計算回路を持っているので、`float` なら速く計算できます。`double` は遅いままです。

## 定数と名前

```cpp
constexpr uint LED_PIN = 25;           // ビルドのときに決まる定数。#define より安全
constexpr int HZ = 25;
constexpr int N = HZ * 2;              // 定数どうしの計算もビルドのときに済む

enum class Mode { Idle, Measure, Send };   // 状態に名前を付ける
Mode mode = Mode::Idle;
```

- 数字を直接書かず、`constexpr` で名前を付けます。ピン番号を変えるとき、1か所直すだけで済みます
- 状態や種類は `enum class` で名前を付けます。`0`、`1`、`2` のような数より、読みやすくまちがえにくくなります

## メモリの置き場所

9章のおさらいです。製品では、**メモリの使い方をビルドのときに決めておく**のが基本です。

| 置き場所 | 書き方 | 決まるとき | 注意 |
| --- | --- | --- | --- |
| フラッシュ（読むだけ） | `static const` / `constexpr` の配列 | ビルド | RAM を使わない。大きな表はここ |
| 静的（RAM） | 関数の外の変数、`static` | ビルド | 大きな配列はここ |
| スタック（RAM） | 関数の中の変数 | 実行中 | 小さい（数KB）。大きな配列を作るとあふれる |
| ヒープ（RAM） | `new`、`std::vector`、`std::string` | 実行中 | すき間ができて、長く動かすと足りなくなる |

```cpp
static const float table[256] = { /* ... */ };   // フラッシュに置かれる（RAM を使わない）
float samples[1000];                             // 静的。4KB
Mpu6050 mpu(i2c0);                               // クラスも関数の外に置ける

void loop_once() {
    float fe[8];                                 // 小さいものはスタックでよい
    // float big[5000];                          // ← スタックがあふれる
}
```

ビルドしたプログラムが RAM をどれだけ使うかは、コマンドでビルドしたときに次のように確かめられます。

```bash
arm-none-eabi-size build/blink.elf
```

```text
   text    data     bss     dec     hex filename
  31744      0   3592   35336    8a08 build/blink.elf
```

`text` はフラッシュ、`data + bss` が RAM（静的）の使用量です。264KB（270336 バイト）から、スタックの分（数KB）を引いた残りまで使えます。

## 使ってよい標準ライブラリ

| 使ってよい | 理由 |
| --- | --- |
| `<cstdint>`、`<cstdio>`（`printf`）、`<cstring>`（`memcpy`） | 小さい |
| `<cmath>`（`sqrtf` など） | 小数の計算 |
| `<array>`（`std::array`） | 大きさが決まった配列。範囲を確かめる `at()` もある |
| `<algorithm>`（`std::min`、`std::max`、`std::clamp`、`std::sort`） | メモリを使わない |
| `<optional>`（`std::optional`） | 「値がない」を表せる（下の「エラーの扱い」） |

| 避ける | 理由 |
| --- | --- |
| `<iostream>`（`std::cout`） | プログラムが数百KB 大きくなる。`printf` を使う |
| `std::vector`、`std::string`、`std::map` | ヒープを使う。使うなら最初に `reserve` して増やさない |
| `try` / `throw` | Pico SDK では例外を使わない設定（`PICO_CXX_ENABLE_EXCEPTIONS=0`） |
| `std::thread`、`std::mutex` | OS がないので使えない。2つのコアは16章 |
| `new` / `delete` | ヒープを使う。最初に1回だけならよい |

## エラーの扱い

例外を使わないので、**戻り値**でエラーを知らせます。

```cpp
#include <optional>

// 方法1: 成功したら true。結果は引数（参照）で返す
bool read_temp(float& out);

// 方法2: 値がないことを std::optional で表す
std::optional<float> read_temp();

if (auto t = read_temp()) {          // 値があるときだけ中に入る
    printf("%.1f C\n", *t);
} else {
    printf("読めませんでした\n");
}
```

エラーの種類を分けたいときは、`enum class` を返します。

```cpp
enum class SensorError { None, NotFound, BadCrc, Timeout };

SensorError read_sht31(float& temp, float& hum);
```

- Pico SDK の関数も、エラーのときは負の数（`PICO_ERROR_GENERIC` など）を返します。**戻り値は必ず確かめます**
- エラーのときにどうするか（もう一度読む、前の値を使う、記録に残す）を決めておくのが、製品では大切です

## クラスでセンサーを扱う

センサーごとにクラスを作ると、使う側のコードが短くなり、センサーを替えるときも直すところが少なくなります。7章の `Mpu6050` がこの形です。

```cpp
class Sht31 {
public:
    explicit Sht31(i2c_inst_t* i2c, uint8_t addr = 0x44) : i2c_(i2c), addr_(addr) {}

    bool read(float& temp, float& hum);   // 中身は8章のコード

private:
    i2c_inst_t* i2c_;                     // どの I2C か
    uint8_t addr_;                        // アドレス
};
```

- コンストラクタ（`Sht31(...)`）では I2C の通信をしません。関数の外に置いたオブジェクトは `main` より前に作られ、そのときはまだ I2C の準備ができていないためです。通信は `begin()` などの関数で行います
- `explicit` は、思わぬ型の変換を防ぐ印です。引数が1つのコンストラクタには付けます

## ファイルを分ける

プログラムが長くなったら、ファイルを分けます。

| ファイル | 中身 |
| --- | --- |
| `sht31.h` | クラスの形（宣言） |
| `sht31.cpp` | 関数の中身 |
| `main.cpp` | `#include "sht31.h"` して使う |

Pico Studio はコード欄の1ファイルだけをビルドするので、分けたいときは **`.h` に中身まで書きます**（クラスの中に関数を書くか、`inline` を付ける）。
`#pragma once` を先頭に書くと、同じ `.h` を2回読み込んでもエラーになりません。

```cpp
// filter.h  ―「PC に保存」で ~/apps/pico-cpp/filter.h に保存すると、#include "filter.h" で使える
#pragma once

// 移動平均。直近 N 個の平均を返す
template <int N>
class MovingAverage {
public:
    float add(float v) {
        sum_ += v - buf_[i_];
        buf_[i_] = v;
        i_ = (i_ + 1) % N;
        if (count_ < N) count_++;
        return sum_ / count_;
    }

private:
    float buf_[N] = {};
    float sum_ = 0;
    int i_ = 0, count_ = 0;
};
```

`.cpp` に分けたいときは、14章の「コマンドでビルドする」で `add_executable(app main.cpp sht31.cpp)` のように書きます。

## 待たない書き方（状態機械）

`sleep_ms` で待っている間、ピコはほかのことができません。
「LED を 0.5秒ごとに点滅させながら、ボタンも見て、1秒ごとに温度も測る」ように、いくつもの動きを同時に進めたいときは、**時刻を見て、その時が来たものだけを行う**書き方にします。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/adc.h"

constexpr uint LED_PIN = 25;
constexpr uint BTN_PIN = 24;

enum class Mode { Slow, Fast, Off };   // LED の点滅のしかた

// 「period_ms ごとに true になる」タイマー
class Every {
public:
    explicit Every(uint32_t period_ms) : period_(period_ms), next_(make_timeout_time_ms(period_ms)) {}
    bool ready() {
        if (absolute_time_diff_us(get_absolute_time(), next_) > 0) return false;   // まだ時間ではない
        next_ = delayed_by_ms(next_, period_);
        return true;
    }
    void set_period(uint32_t ms) { period_ = ms; }

private:
    uint32_t period_;
    absolute_time_t next_;
};

int main() {
    stdio_init_all();
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_init(BTN_PIN);
    gpio_set_dir(BTN_PIN, GPIO_IN);
    gpio_pull_up(BTN_PIN);
    adc_init();
    adc_set_temp_sensor_enabled(true);
    adc_select_input(4);

    Mode mode = Mode::Slow;
    Every blink(500), measure(1000), button(20);
    bool led = false, last_pressed = false;

    while (true) {
        if (button.ready()) {                       // 20ms ごとにボタンを見る
            bool pressed = !gpio_get(BTN_PIN);
            if (pressed && !last_pressed) {         // 押した瞬間だけ
                mode = (mode == Mode::Slow) ? Mode::Fast : (mode == Mode::Fast) ? Mode::Off : Mode::Slow;
                blink.set_period(mode == Mode::Fast ? 100 : 500);
                printf("モード: %s\n", mode == Mode::Slow ? "ゆっくり" : mode == Mode::Fast ? "速く" : "消す");
            }
            last_pressed = pressed;
        }
        if (blink.ready()) {                        // 点滅
            led = (mode == Mode::Off) ? false : !led;
            gpio_put(LED_PIN, led);
        }
        if (measure.ready()) {                      // 1秒ごとに温度
            float v = adc_read() * 3.3f / 4096;
            printf("温度 %.1f C\n", 27.0f - (v - 0.706f) / 0.001721f);
        }
        sleep_ms(1);                                // 少し休む（電力を下げる）
    }
}
```

USR ボタンを押すたびに、LED の点滅が「ゆっくり → 速く → 消す」と変わります。その間も、温度は1秒ごとに出続けます。

| 考え方 | 内容 |
| --- | --- |
| くり返しの中で待たない | `sleep_ms(500)` のような長い待ちを入れない。時刻を見て、時が来たものだけ行う |
| 状態を変数で持つ | 「今どのモードか」を `Mode mode` で覚えておく |
| 押した瞬間を見つける | 前回の値（`last_pressed`）と比べて、離した状態から押した状態に変わったときだけ動く |
| 20ms ごとに見る | ボタンの接点が震えて、1回押しても何回も押したように見える（チャタリング）のを防ぐ |

この形は、12章の `asyncio` と同じ考え方です。もっと正確な時刻で動かしたいときは、16章の割り込みを使います。

## まとめ

- 型は `uint8_t`、`int16_t`、`uint32_t` のように大きさが決まったものを使う
- 小数は `float` と `f` 付きの数。たくさん計算するなら整数（mg など）で
- 定数は `constexpr`、状態は `enum class`
- 大きなデータは関数の外（静的）か `static const`（フラッシュ）。`new` や `std::vector` は避ける
- `std::cout`・例外・`std::thread` は使わない。エラーは戻り値（`bool`、`std::optional`、`enum class`）
- センサーはクラスにまとめる。通信はコンストラクタではなく `begin()` で
- いくつもの動きは、時刻を見て進める（状態機械）。長く `sleep_ms` しない
