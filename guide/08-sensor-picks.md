# 8. おすすめのセンサー

## この章でわかること

- 最初に使うセンサーと、農業で使うセンサー
- センサーを選ぶときの注意
- SHT31 と土壌水分センサーのつなぎ方と読み方
- 商品の説明にある「ADC コンバータが必要」の意味

## 最初に使うなら

次の2つがおすすめです。どちらも I2C でつなげます。配線は6章、コードは7章にそのまま載っています。

| センサー | 測れるもの | 向いている用途 |
| --- | --- | --- |
| **MPU-6050（GY-521）** | 加速度、傾き、回転 | 動きの測定。牛の行動判定（10章の機械学習まで使える） |
| **BMP280** | 気圧、温度 | 高さの変化、気温 |

## 農業で使うなら

次の2つも候補です。つなぎ方とコードは、この章のあとの節に載せています。

| センサー | 測れるもの | つなぎ方 | 向いている用途 |
| --- | --- | --- | --- |
| **SHT31** | 温度、湿度 | I2C | ハウスの中の環境測定 |
| **静電容量式の土壌水分センサー** | 土の水分 | ADC（5章） | 水やりの目安。電極がさびにくい |

## 選ぶときの注意

- **3.3V で使えるものを選ぶ。** 電源はピコの 3V3(OUT) から取ります（6章）
- **はんだ付けが必要か確かめる。** モジュールは、ピンが別になっていて、はんだ付けが必要なものが多いです（6章）
- **同じ I2C の線に複数つなぐときは、アドレスが重ならないものを選ぶ。** アドレスは6章の I2C スキャンで確かめられます

> この2つのコードは、実際のセンサーではまだ確かめていません。動かないときは、購入したモジュールの説明と見比べてください。

## SHT31 のつなぎ方と読み方

MPU-6050 と同じ I2C の線に並べてつなげます。USB を抜いてから配線します。モジュールによってピンの名前が違うので、購入した商品の表示に合わせます。

| ピコ | SHT31 |
| --- | --- |
| 3V3(OUT)（36番） | VIN（または VCC） |
| GND（38番） | GND |
| GP4 / I2C0 SDA（6番） | SDA |
| GP5 / I2C0 SCL（7番） | SCL |

I2C のアドレスは `0x44` です（ADDR ピンを 3.3V につなぐと `0x45`）。6章の I2C スキャンで確かめられます。

<!-- python -->

```python run
from machine import Pin, I2C
import time

ADDR = 0x44
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

for i in range(5):
    i2c.writeto(ADDR, bytes([0x24, 0x00]))   # 1回測るように指示する
    time.sleep_ms(20)                        # 測り終わるのを待つ
    d = i2c.readfrom(ADDR, 6)                # 温度2バイト、確認用1バイト、湿度2バイト、確認用1バイト
    temp = -45 + 175 * ((d[0] << 8) | d[1]) / 65535
    hum = 100 * ((d[3] << 8) | d[4]) / 65535
    print("温度: {:.1f} ℃  湿度: {:.1f} %".format(temp, hum))
    time.sleep(1)
```

<!-- /python -->
<!-- cpp -->

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

constexpr uint8_t ADDR = 0x44;

// 確認用のバイト（CRC）を計算する。データシートの決まり: 多項式 0x31、初期値 0xFF
uint8_t crc8(const uint8_t* data, int len) {
    uint8_t crc = 0xFF;
    for (int i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (crc << 1) ^ 0x31 : (crc << 1);
    }
    return crc;
}

int main() {
    stdio_init_all();
    i2c_init(i2c0, 100 * 1000);
    gpio_set_function(4, GPIO_FUNC_I2C);
    gpio_set_function(5, GPIO_FUNC_I2C);
    gpio_pull_up(4);
    gpio_pull_up(5);

    while (true) {
        const uint8_t cmd[2] = {0x24, 0x00};             // 1回測るように指示する
        i2c_write_blocking(i2c0, ADDR, cmd, 2, false);
        sleep_ms(20);                                     // 測り終わるのを待つ
        uint8_t d[6];                                     // 温度2・確認1・湿度2・確認1
        if (i2c_read_blocking(i2c0, ADDR, d, 6, false) != 6) {
            printf("読み取りに失敗しました\n");
        } else if (crc8(d, 2) != d[2] || crc8(d + 3, 2) != d[5]) {
            printf("確認用のバイトが合いません（ノイズ）\n");
        } else {
            float temp = -45 + 175 * ((d[0] << 8) | d[1]) / 65535.0f;
            float hum = 100 * ((d[3] << 8) | d[4]) / 65535.0f;
            printf("温度: %.1f C  湿度: %.1f %%\n", temp, hum);
        }
        sleep_ms(1000);
    }
}
```

- 製品では、確認用のバイト（CRC）を必ず確かめます。線が長いと、ノイズで値が化けることがあるためです
- `printf` で `%` を出すときは `%%` と書きます

<!-- /cpp -->

## 土壌水分センサーのつなぎ方と読み方

アナログ入力（ADC）で読みます。ピコの ADC は 3.3V までなので、電源は必ず 3V3(OUT) からとります。5V で動かすと、出力の電圧が高くなって、ピコを壊すことがあります。

| ピコ | 土壌水分センサー |
| --- | --- |
| 3V3(OUT)（36番） | VCC |
| GND（38番） | GND |
| GP26 / ADC0（31番） | AOUT |

<!-- python -->

```python run
from machine import ADC
import time

DRY = 50000    # 空気中に置いたときの値（自分のセンサーの値に書き換える）
WET = 20000    # 水に入れたときの値（自分のセンサーの値に書き換える）

sensor = ADC(26)
for i in range(10):
    value = sensor.read_u16()
    percent = (DRY - value) / (DRY - WET) * 100
    percent = max(0, min(100, percent))
    print("値: {}  水分: {:.0f} %".format(value, percent))
    time.sleep(1)
```

<!-- /python -->
<!-- cpp -->

```cpp run
#include <algorithm>
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/adc.h"

constexpr int DRY = 3100;    // 空気中に置いたときの値（自分のセンサーの値に書き換える）
constexpr int WET = 1250;    // 水に入れたときの値（自分のセンサーの値に書き換える）

int main() {
    stdio_init_all();
    adc_init();
    adc_gpio_init(26);
    adc_select_input(0);

    while (true) {
        // 16回読んで平均する（値のふらつきを減らす）
        int sum = 0;
        for (int i = 0; i < 16; i++) sum += adc_read();
        int value = sum / 16;
        float percent = (DRY - value) * 100.0f / (DRY - WET);
        percent = std::clamp(percent, 0.0f, 100.0f);     // 0〜100 の間におさめる
        printf("値: %d  水分: %.0f %%\n", value, percent);
        sleep_ms(1000);
    }
}
```

C++ の `adc_read()` は 0〜4095 なので、`DRY` と `WET` も 0〜4095 の範囲の値になります（Python の値の 16分の1くらい）。

<!-- /cpp -->

値はセンサーごとに違うので、最初に調べます。

1. センサーを空気中に置いて実行し、出た値を `DRY` に書く
2. センサーを水に入れて実行し、出た値を `WET` に書く。水に入れてよいのは、線の目印より下だけ
3. 土に差して実行する

このセンサーは、水分が多いほど値が小さくなります。出てくる % は、乾いたときと濡れたときの間のどのあたりかを示す目安です。

## 商品の説明の読み方

### 「ADC コンバータが必要」と書いてあるとき

ADC は Analog-to-Digital Converter（アナログからデジタルへの変換器）の略です。センサーが出す電圧を、コンピューターが読める数値に変える部品です。

| ボード | ADC | アナログのセンサーに必要なもの |
| --- | --- | --- |
| ピコ | 内蔵（GP26、GP27、GP28） | センサーだけ |
| ラズパイ | なし | 外付けの ADC（MCP3008 など） |

商品の説明に「Raspberry Pi には ADC コンバータが必要」とあっても、これは Linux が動くラズパイの話です。ピコでは要りません。

### 「3.3〜5.5V で動く」と書いてあるとき

5V でも動くと書いてあっても、ピコでは **3.3V** で使います。出力の電圧が 3.3V を超えると、ピコの ADC を壊すことがあります。

### 線の色

線の色は商品によって違うことがあります。色ではなく、**基板に書かれた文字**（VCC、GND、AOUT）に合わせてつなぎます。

### 同じ見た目でも中身が違うことがある

安い土壌水分センサーは、同じ見た目でも基板の部品が違う個体があると言われています。タイマーの IC が NE555 の個体は、3.3V では動かないことがあります。
届いたら、空気中と水中で値が大きく変わるかを確かめてください。
## まとめ

- 最初のセンサーは MPU-6050 と BMP280 がおすすめ
- 温度と湿度は SHT31、土の水分は静電容量式の土壌水分センサー
- どのセンサーも 3.3V で使えるかを確かめて、3V3(OUT) から電源をとる
- ピコには ADC が内蔵されているので、「ADC コンバータ」は要らない
