# 16. 割り込み・タイマー・2つのコア

## この章でわかること

- 割り込みとは何か、ポーリングとの違い
- ボタンが押された瞬間に動く（GPIO の割り込み）
- 決まった間隔で正確に動く（くり返しタイマー）
- 割り込みと `main` の間で、データを安全に受け渡す（リングバッファ）
- 2つのコアで別々の処理を動かす
- 割り込みの中でしてはいけないこと

15章の「待たない書き方」がわかっている前提です。

## 割り込みとは

ボタンを読むには、2つの方法があります。

| 方法 | しくみ | 良いところ | 注意 |
| --- | --- | --- | --- |
| ポーリング | くり返しの中で、何度もピンを読みに行く | わかりやすい | 読みに行く間隔より短い変化を見のがす。ずっと動いているので電力を使う |
| 割り込み | ピンが変わった瞬間に、ピコが今の処理を中断して、決めておいた関数を呼ぶ | 見のがさない。待っている間は休める | 割り込みの関数は短く書く。データの受け渡しに注意 |

割り込みで呼ばれる関数を、**割り込みハンドラ**（コールバック）といいます。

## ボタンが押された瞬間に動く

USR ボタン（GP24）が押されるたびに、回数を数えます。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint BTN_PIN = 24;

volatile uint32_t press_count = 0;     // 割り込みで書き換える変数には volatile を付ける
volatile uint32_t last_press_ms = 0;

// ボタンが押されると呼ばれる（割り込みハンドラ）
void on_button(uint gpio, uint32_t events) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    if (now - last_press_ms < 50) return;          // 50ms 以内の2回目は、接点の震え（チャタリング）として無視
    last_press_ms = now;
    press_count++;
}

int main() {
    stdio_init_all();
    gpio_init(BTN_PIN);
    gpio_set_dir(BTN_PIN, GPIO_IN);
    gpio_pull_up(BTN_PIN);
    // 1 → 0 に変わったとき（押したとき）に on_button を呼ぶ
    gpio_set_irq_enabled_with_callback(BTN_PIN, GPIO_IRQ_EDGE_FALL, true, &on_button);

    uint32_t shown = 0;
    while (true) {
        if (press_count != shown) {                // printf は割り込みの外で行う
            shown = press_count;
            printf("押された回数: %u\n", static_cast<unsigned>(shown));
        }
        sleep_ms(10);
    }
}
```

| コード | 意味 |
| --- | --- |
| `gpio_set_irq_enabled_with_callback(pin, 種類, true, &関数)` | ピンの割り込みを有効にして、呼ぶ関数を決める |
| `GPIO_IRQ_EDGE_FALL` | 1 → 0 に変わったとき（プルアップのボタンを押したとき） |
| `GPIO_IRQ_EDGE_RISE` | 0 → 1 に変わったとき（離したとき）。`\|` で両方も指定できる |
| `volatile` | 「この変数は、いつ変わるかわからない」という印。付けないと、`main` が古い値を見続けることがある |

> 割り込みハンドラは、**全部のピンで1つ**です。2本目のピンは `gpio_set_irq_enabled(pin, 種類, true)` で有効にし、ハンドラの中で引数の `gpio` を見て分けます。

## 割り込みの中でしてはいけないこと

割り込みハンドラが動いている間、`main` は止まっています。ほかの割り込みも待たされます。

| してはいけない | 理由 |
| --- | --- |
| `printf` | 時間がかかり、USB の処理とぶつかることがある |
| `sleep_ms` などの待ち | その間、全部が止まる |
| 長い計算、長いループ | 同じ |
| `new` / `malloc` | `main` と同時に使うと、こわれることがある |

ハンドラでは、**値を読んで変数やバッファに入れるだけ**にして、重い処理は `main` で行います。

## 決まった間隔で正確に動く

7章では `sleep_until` で間隔をそろえましたが、くり返しの中でほかの処理（判定や送信）に時間がかかると、次の測定が遅れます。
**くり返しタイマー**を使うと、ほかの処理をしていても、決まった間隔で関数が呼ばれます。

次のプログラムは、100Hz（10ms ごと）で MPU-6050 を読み、`main` では1秒ごとに平均を出します。
読んだ値は、割り込みから `main` へ **リングバッファ** で渡します。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/sync.h"
#include "mpu6050.h"

// 割り込み（書く側）と main（読む側）の間でデータを渡す、輪になった入れ物
template <typename T, int N>
class RingBuffer {
public:
    bool push(const T& v) {                    // 割り込みから呼ぶ
        int next = (head_ + 1) % N;
        if (next == tail_) return false;       // いっぱい（読む側が遅れている）
        buf_[head_] = v;
        head_ = next;
        return true;
    }
    bool pop(T& v) {                           // main から呼ぶ
        uint32_t irq = save_and_disable_interrupts();   // 取り出す間だけ割り込みを止める
        bool ok = tail_ != head_;
        if (ok) {
            v = buf_[tail_];
            tail_ = (tail_ + 1) % N;
        }
        restore_interrupts(irq);
        return ok;
    }

private:
    T buf_[N];
    volatile int head_ = 0, tail_ = 0;
};

struct Sample { float ax, ay, az; };

Mpu6050 mpu(i2c0);
RingBuffer<Sample, 256> samples;               // 2.5秒分ためられる
volatile uint32_t dropped = 0;

// 10ms ごとに呼ばれる
bool on_timer(repeating_timer_t*) {
    Sample s;
    if (mpu.read_accel(s.ax, s.ay, s.az) && !samples.push(s)) dropped++;
    return true;                               // true を返すと、くり返す
}

int main() {
    stdio_init_all();
    mpu.begin(4, 5);

    repeating_timer_t timer;
    add_repeating_timer_ms(-10, on_timer, nullptr, &timer);   // -10 = 前回の開始から 10ms ごと

    float sum = 0;
    int n = 0;
    absolute_time_t next = make_timeout_time_ms(1000);
    while (true) {
        Sample s;
        while (samples.pop(s)) {               // たまっている分を全部取り出す
            sum += s.az;
            n++;
        }
        if (absolute_time_diff_us(get_absolute_time(), next) <= 0) {
            printf("1秒で %d 回  z の平均 %.3f g  取りこぼし %u\n", n, n ? sum / n : 0.0f,
                   static_cast<unsigned>(dropped));
            sum = 0;
            n = 0;
            next = delayed_by_ms(next, 1000);
        }
        sleep_ms(5);
    }
}
```

1秒ごとに、次のように出ます。

```text
1秒で 100 回  z の平均 1.002 g  取りこぼし 0
```

| コード | 意味 |
| --- | --- |
| `add_repeating_timer_ms(-10, 関数, nullptr, &timer)` | 10ms ごとに関数を呼ぶ。マイナスは「前回の開始から」、プラスは「前回の終わりから」 |
| `bool on_timer(repeating_timer_t*)` | タイマーで呼ばれる関数。`false` を返すと止まる |
| `repeating_timer_t timer;` | タイマーの情報。**動いている間は消えないところ**に置く（`main` の中なら、`main` は終わらないので大丈夫） |
| `RingBuffer<Sample, 256>` | `Sample` を256個までためられる入れ物。いっぱいになったら、新しいものを捨てて数える |
| `save_and_disable_interrupts()` | 取り出す途中で割り込みが入り、`head_` と `tail_` がずれないように、短い間だけ止める |

- I2C の読み取り（6バイトで約0.2ms）を割り込みの中で行っています。0.2ms なら問題ありませんが、もっと長くかかる処理はフラグだけ立てて `main` で行います
- 1回だけ呼びたいときは `add_alarm_in_ms(ms, 関数, nullptr, false)` を使います

## 2つのコアを使う

ピコのチップにはコアが2つあり、本当に同時に2つの処理を動かせます。`main` が動くのがコア0、もう1つがコア1です。
次のプログラムは、コア1が測定、コア0が表示を受け持ちます。

```cpp run
#include <cstdio>
#include <cstring>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "mpu6050.h"

Mpu6050 mpu(i2c0);

// コア1: 50Hz で測って、1秒ごとの「動きの大きさ」をコア0に送る
void core1_main() {
    mpu.begin(4, 5);
    absolute_time_t next = get_absolute_time();
    float sum = 0;
    for (int n = 1;; n++) {
        float ax, ay, az;
        mpu.read_accel(ax, ay, az);
        sum += (ax * ax + ay * ay + az * az);
        if (n % 50 == 0) {
            float mean = sum / 50;
            uint32_t bits;
            memcpy(&bits, &mean, 4);               // float を 32ビットの数として送る
            multicore_fifo_push_blocking(bits);
            sum = 0;
        }
        next = delayed_by_ms(next, 20);
        sleep_until(next);
    }
}

int main() {
    stdio_init_all();
    multicore_launch_core1(core1_main);            // コア1で core1_main を動かし始める

    while (true) {
        uint32_t bits = multicore_fifo_pop_blocking();   // コア1から届くまで待つ
        float mean;
        memcpy(&mean, &bits, 4);
        printf("動きの大きさ（加速度の2乗の平均）: %.3f\n", mean);
    }
}
```

| コード | 意味 |
| --- | --- |
| `multicore_launch_core1(関数)` | コア1で関数を動かす。関数は終わらないようにする |
| `multicore_fifo_push_blocking(数)` | もう片方のコアに 32ビットの数を送る。いっぱいなら空くまで待つ |
| `multicore_fifo_pop_blocking()` | 届いた数を受け取る。届くまで待つ |
| `memcpy(&bits, &mean, 4)` | `float` の中身をそのまま `uint32_t` に写す（値の変換はしない） |

### コアの間でデータを分け合うとき

FIFO は8個までしかためられません。大きなデータを分け合うときは、変数を共有して、**同時に触らないように鍵（クリティカルセクション）をかけます**。

```cpp
#include "pico/sync.h"

critical_section_t lock;
float shared_features[8];

// 最初に1回: critical_section_init(&lock);

// 書く側（コア1）
critical_section_enter_blocking(&lock);
memcpy(shared_features, fe, sizeof(fe));
critical_section_exit(&lock);

// 読む側（コア0）
critical_section_enter_blocking(&lock);
memcpy(fe, shared_features, sizeof(fe));
critical_section_exit(&lock);
```

### 2つのコアで気をつけること

- `printf` は片方のコアだけで使います。両方から使うと、文字が混ざることがあります
- 同じ I2C を両方のコアから使わないようにします。センサーは片方のコアにまかせます
- フラッシュに書くとき（9章・17章）は、もう片方のコアも止める必要があります。コア1で `multicore_lockout_victim_init()` を呼んでおき、書く側で `multicore_lockout_start_blocking()` と `multicore_lockout_end_blocking()` ではさみます

## どれを使うか

| やりたいこと | 方法 |
| --- | --- |
| いくつかの動きを、だいたいの間隔で進める | 15章の状態機械（時刻を見て進める） |
| ボタンやセンサーの信号を見のがしたくない | GPIO の割り込み |
| 決まった間隔で正確に測りたい | くり返しタイマー + リングバッファ |
| 重い計算（判定など）と測定を、本当に同時に動かしたい | 2つのコア |
| もっと速く（数十kHz 以上）データを取りたい | DMA（CPU を使わずにデータを運ぶ回路）。[pico-examples の adc/dma_capture](https://github.com/raspberrypi/pico-examples/tree/master/adc/dma_capture) |

## まとめ

- 割り込みは、信号が変わった瞬間や決まった時刻に、関数を呼んでもらうしくみ
- GPIO は `gpio_set_irq_enabled_with_callback`、くり返しは `add_repeating_timer_ms`
- 割り込みで書き換える変数には `volatile`。ハンドラは短く、`printf` や待ちは入れない
- 割り込みと `main` の受け渡しはリングバッファ。取り出す間だけ割り込みを止める
- 2つのコアは `multicore_launch_core1`。受け渡しは FIFO か、鍵をかけた共有の変数
