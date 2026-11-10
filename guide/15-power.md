# 17. 省電力と長く動かすための工夫

## この章でわかること

- ピコの電力を減らす方法と、それぞれの効き目
- 電池の電圧を測って、残りを知る方法
- 止まったときに自動で再起動する（ウォッチドッグ）
- 再起動の理由を記録する
- 設定やキャリブレーションの値を、電源を切っても残す（フラッシュ）

首輪のように電池で何か月も動かす製品では、この章の内容が欠かせません。電池の計算のしかたは13章にあります。

## 電力を減らす方法

電力は、**使っている時間 × 使っている電流**で決まります。減らし方は大きく3つです。

1. 動いている間の電流を減らす（クロックを下げる、使わない回路を止める）
2. 待っている間の電流を減らす（休む）
3. 動いている時間を短くする（処理をまとめる、送る回数を減らす）

| 方法 | 効き目の目安 | 手間 |
| --- | --- | --- |
| 待つ間は `sleep_ms` / `sleep_until` で休む | 中 | 小（もう使っている） |
| CPU のクロックを下げる | 中 | 小 |
| センサーを、測らない間は寝かせる | 中〜大（センサーによる） | 小 |
| 送る回数を減らす（まとめて送る） | 大（無線を使うとき） | 小 |
| USB を使わない（製品では `printf` を UART にするか、なくす） | 小〜中 | 小 |
| DORMANT（深い眠り）にする | 大 | 大（pico-extras が必要） |
| 電源の回路を選ぶ（効率のよいレギュレーター） | 大 | 基板の設計 |

数字は、ボードやつないだ部品で大きく変わります。**必ず自分の回路で電流を測って**確かめます（下の「電流を測る」）。

### 待つ間は休む

`sleep_ms` や `sleep_until` は、待っている間 CPU を休ませます（`__wfe` という命令で、割り込みが来るまで止まる）。
`while` の中で何もせずに時刻を見続ける書き方（ビジーループ）は、電力を使い続けるのでやめます。

```cpp
// よくない: 待っている間も CPU が全力で動く
while (absolute_time_diff_us(get_absolute_time(), next) > 0) {}

// よい: 待っている間は休む
sleep_until(next);
```

### クロックを下げる

ピコの CPU は 125MHz（Pico 2 は 150MHz）で動いています。測定と判定だけなら、ずっと遅くても間に合います。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/clocks.h"

int main() {
    set_sys_clock_khz(48000, true);    // CPU を 48MHz にする（stdio_init_all より前に）
    stdio_init_all();

    while (true) {
        printf("CPU のクロック: %u Hz\n", static_cast<unsigned>(clock_get_hz(clk_sys)));
        sleep_ms(1000);
    }
}
```

- `set_sys_clock_khz(48000, true)` の `true` は「その速さにできなければ止まる」。作れない速さもあるので、48000、64000、96000 などを使います
- クロックを変えるのは、`stdio_init_all()` やタイマー、PWM の設定より**前**に行います。PWM や UART の速さはクロックから計算されるためです
- USB は別のクロックで動いているので、48MHz にしても `printf` は使えます

### センサーを寝かせる

センサーも電気を使います。たとえば MPU-6050 は、ジャイロを使わないなら止められます。

```cpp
// MPU-6050: ジャイロの3軸を止める（PWR_MGMT_2 = 0x6C の下位3ビット）
uint8_t buf[2] = {0x6C, 0x07};
i2c_write_blocking(i2c0, 0x68, buf, 2, false);
```

どのレジスタで寝かせられるかは、センサーのデータシートの「Power Management」や「Low Power」の項目に書いてあります。

### DORMANT（深い眠り）

もっと電流を減らしたいときは、クロックをほとんど止める **DORMANT** や **SLEEP** を使います。ボタンや RTC（時計）の割り込みで目を覚まします。
Pico SDK の本体には入っておらず、[pico-extras](https://github.com/raspberrypi/pico-extras) の `pico_sleep` を使います。Pico Studio のビルドでは使えないので、14章の「コマンドでビルドする」の方法で、pico-extras を読み込むように `CMakeLists.txt` を書きます。
例は [pico-playground の sleep](https://github.com/raspberrypi/pico-playground/tree/master/sleep) にあります。

### 電流を測る

電池とピコの VSYS の間に、電流計（テスターの電流のレンジ）か、USB の電流チェッカーをはさんで測ります。

| 状態 | 測るところ |
| --- | --- |
| 動いているとき | 測定・判定の間 |
| 休んでいるとき | `sleep_until` で待っている間 |
| 送っているとき | 無線で送っている間（Pico W など） |

それぞれの電流と時間の割合から、平均の電流を出し、13章の計算で電池の持ちを見積もります。

## 電池の電圧を測る

公式の Pico では、電源の電圧（VSYS）を3分の1にしたものが **GP29（ADC3）** につながっています。これを読むと、電池の残りの目安がわかります。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/adc.h"

int main() {
    stdio_init_all();
    adc_init();
    adc_gpio_init(29);                 // GP29 = VSYS / 3
    adc_select_input(3);

    while (true) {
        uint32_t sum = 0;
        for (int i = 0; i < 16; i++) sum += adc_read();
        float vsys = (sum / 16.0f) * 3.3f / 4095 * 3;   // 3分の1にされているので、3倍に戻す
        printf("VSYS: %.2f V\n", vsys);
        sleep_ms(1000);
    }
}
```

- USB につないでいるときは、約 5V から少し下がった値（4.7V 前後）が出ます
- **Pico W / Pico 2 W** では、GP29 を無線のチップと共有しているので、この方法そのままでは読めません（無線を使っている間は読まない、などの工夫が必要です）
- 電池の電圧が下がってきたら、記録を止めて大事なデータを保存する、送る回数を減らす、などを決めておきます

## 止まったら自動で再起動する（ウォッチドッグ）

製品では、思いがけないことでプログラムが止まることがあります（センサーの通信が返ってこない、配列の外に書いた、など）。
**ウォッチドッグ**は、決めた時間のうちに「動いているよ」の合図（`watchdog_update()`）が来なければ、ピコを再起動する見張り役です。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/watchdog.h"

constexpr uint LED_PIN = 25;
constexpr uint BTN_PIN = 24;

int main() {
    stdio_init_all();
    sleep_ms(1500);
    if (watchdog_caused_reboot()) {
        printf("ウォッチドッグで再起動しました\n");
    } else {
        printf("普通に起動しました\n");
    }

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_init(BTN_PIN);
    gpio_set_dir(BTN_PIN, GPIO_IN);
    gpio_pull_up(BTN_PIN);

    watchdog_enable(2000, true);       // 2秒合図がなければ再起動。true = デバッグ中は止める

    while (true) {
        gpio_put(LED_PIN, !gpio_get(LED_PIN));
        if (!gpio_get(BTN_PIN)) {
            printf("ボタンが押されたので、わざと止まります\n");
            while (true) {}            // 止まったふり（合図を送らない）
        }
        watchdog_update();             // 「動いているよ」の合図
        sleep_ms(200);
    }
}
```

書き込むと LED が点滅し、USR ボタンを押すと止まります。2秒後にピコが再起動し、「ウォッチドッグで再起動しました」と出ます。

| コード | 意味 |
| --- | --- |
| `watchdog_enable(2000, true)` | 2000ms のうちに合図がなければ再起動する。最大は約8秒 |
| `watchdog_update()` | 合図を送る。くり返しの中で、決めた時間より短い間隔で呼ぶ |
| `watchdog_caused_reboot()` | 前回の再起動がウォッチドッグによるものなら `true` |

- 時間は、くり返し1回にかかる時間（長い処理も含めて）より十分長くします
- `watchdog_update()` は、**全部の処理が正しく進んだとき**だけ呼ぶようにします。割り込みの中で呼ぶと、`main` が止まっていても合図が出てしまうので意味がありません
- 再起動の回数や理由を記録しておくと、現場で何が起きたか後から調べられます（下の「設定を残す」と同じ方法で、フラッシュに数を残す）

## 設定を残す（フラッシュ）

センサーのキャリブレーションの値（9章の土壌水分センサーの `DRY` と `WET` など）や、牛の番号は、電源を切っても残したいものです。
9章と同じ方法で、フラッシュの**最後の1セクター（4096バイト）**に保存します。

読み込んだ値が正しいかを確かめるために、**目印（マジックナンバー）**と**確認用の数（CRC など）**を一緒に保存します。初めて起動したときや、書いている途中で電源が切れたときに、こわれた値を使わないためです。

```cpp run
#include <cstddef>
#include <cstdio>
#include <cstring>
#include "pico/stdlib.h"
#include "hardware/flash.h"
#include "hardware/sync.h"

struct Settings {
    uint32_t magic;                    // 目印。正しく保存されていれば MAGIC
    uint16_t version;                  // 設定の形を変えたら増やす
    uint16_t cow_id;                   // 牛の番号
    int32_t soil_dry, soil_wet;        // 土壌水分センサーのキャリブレーション
    uint32_t boot_count;               // 起動した回数
    uint32_t check;                    // 確認用の数（上の全部から計算）
};

constexpr uint32_t MAGIC = 0x50494331;  // "PIC1"
constexpr uint16_t VERSION = 1;
constexpr uint32_t OFFSET = PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE;   // 最後の 4096 バイト

// 確認用の数（簡単なハッシュ。FNV-1a）
uint32_t checksum(const Settings& s) {
    auto* p = reinterpret_cast<const uint8_t*>(&s);
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < offsetof(Settings, check); i++) h = (h ^ p[i]) * 16777619u;
    return h;
}

bool load(Settings& s) {
    memcpy(&s, reinterpret_cast<const void*>(XIP_BASE + OFFSET), sizeof(s));
    return s.magic == MAGIC && s.version == VERSION && s.check == checksum(s);
}

void save(Settings& s) {
    s.magic = MAGIC;
    s.version = VERSION;
    s.check = checksum(s);
    static uint8_t page[FLASH_PAGE_SIZE];          // 256 バイトずつしか書けないので、ページに入れる
    memset(page, 0xFF, sizeof(page));
    memcpy(page, &s, sizeof(s));
    uint32_t irq = save_and_disable_interrupts();
    flash_range_erase(OFFSET, FLASH_SECTOR_SIZE);
    flash_range_program(OFFSET, page, FLASH_PAGE_SIZE);
    restore_interrupts(irq);
}

int main() {
    stdio_init_all();
    sleep_ms(1500);

    Settings s;
    if (!load(s)) {
        printf("設定がないので、最初の値を使います\n");
        s = Settings{};
        s.cow_id = 1;
        s.soil_dry = 3100;
        s.soil_wet = 1250;
    }
    s.boot_count++;
    save(s);                                       // 起動した回数を増やして保存

    printf("牛の番号 %u  乾 %d  湿 %d  起動 %u 回目\n", static_cast<unsigned>(s.cow_id), static_cast<int>(s.soil_dry),
           static_cast<int>(s.soil_wet), static_cast<unsigned>(s.boot_count));
    while (true) sleep_ms(1000);
}
```

書き込んだあと、USB を抜き差しするたびに「起動 N 回目」が増えます。

- 1つのセクターを消せるのは約10万回です。**起動のたびや、測るたびに保存しない**ようにします（この例は試すためのものです。製品では、値が変わったときだけ保存します）
- 9章の記録と一緒に使うときは、記録の場所を1セクター前にずらして、重ならないようにします
- 設定の形（`struct`）を変えたら `VERSION` を増やします。古い形の値を、新しい形として読んでしまうのを防げます
- 2つのコアを使っているときは、16章の `multicore_lockout` も使います

## まとめ

- 電力は「電流 × 時間」。待つ間は `sleep_ms` / `sleep_until` で休み、クロックを下げ、センサーを寝かせる
- 深く眠らせるなら pico-extras の `pico_sleep`（コマンドでビルド）
- 効き目は必ず電流を測って確かめる
- 公式 Pico では GP29（ADC3）で電池の電圧（VSYS の 3分の1）がわかる
- ウォッチドッグで、止まったら自動で再起動。合図は全部の処理が正しく進んだときだけ
- 設定はフラッシュの最後のセクターに、目印と確認用の数と一緒に保存する。保存は必要なときだけ
