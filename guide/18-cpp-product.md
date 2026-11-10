# 18. 製品にするための準備

## この章でわかること

- 試作と製品で、何が違うか
- ピコがなくても、PC で判定のロジックをテストする方法
- プログラムに名前とバージョンを入れる方法
- Debug Probe と gdb で、1行ずつ止めて調べる方法
- たくさんのピコに書き込む方法と、1台ずつの番号
- 現場で困らないための工夫と、出荷前のチェックリスト

14〜17章の内容を使います。首輪（13章）を例に説明します。

## 試作と製品の違い

| 項目 | 試作 | 製品 |
| --- | --- | --- |
| 言語 | MicroPython でよい | C++ |
| 動かす場所 | 机の上、PC につないで | 現場で、PC なしで何か月も |
| 止まったとき | 手でリセット | 自動で再起動（17章のウォッチドッグ）して、理由を記録 |
| エラー | 出力欄で見る | 記録に残す。LED の点滅などで知らせる |
| 確かめ方 | 動かして目で見る | テストを書いて、変えるたびに確かめる |
| どのプログラムか | 覚えている | バージョンをプログラムに入れて、あとから調べられる |
| 書き込み | 1台ずつ手で | 手順を決めて、スクリプトで |
| 設定 | コードに直接書く | フラッシュに保存して、1台ずつ変えられる（17章） |

## PC でロジックをテストする

特徴量の計算や判定のような「計算だけの部分」は、ピコがなくても PC でテストできます。
そのために、**ピコに頼らない部分（計算）と、ピコに頼る部分（センサー・ピン）を、別のファイルに分けます**。

```text
~/apps/pico-cpp/
├── features.h          計算だけ（ピコの関数を使わない）← PC でもピコでも使える
├── model.h             判定（10章の train.py で作る）← PC でもピコでも使える
├── collar.cpp          ピコ用（センサーを読んで、features.h と model.h を使う）
└── test_features.cpp   PC 用のテスト
```

### features.h

10章の特徴量の計算を、ピコの関数を使わない形にします。

```cpp
#pragma once
#include <cmath>

// 8個の特徴量を作る。xs, ys, zs は n 個の加速度 [g]
inline void features(const float* xs, const float* ys, const float* zs, int n, float fe[8]) {
    auto mean = [n](const float* a) { float s = 0; for (int i = 0; i < n; i++) s += a[i]; return s / n; };
    auto stdev = [n](const float* a, float m) {
        float s = 0;
        for (int i = 0; i < n; i++) s += (a[i] - m) * (a[i] - m);
        return std::sqrt(s / n);
    };
    float mag[256];                                   // n は 256 以下にする
    for (int i = 0; i < n; i++) mag[i] = std::sqrt(xs[i] * xs[i] + ys[i] * ys[i] + zs[i] * zs[i]);
    float mx = mean(xs), my = mean(ys), mz = mean(zs), mm = mean(mag);
    float diff = 0;
    for (int i = 1; i < n; i++) diff += std::fabs(mag[i] - mag[i - 1]);
    fe[0] = mx; fe[1] = my; fe[2] = mz;
    fe[3] = stdev(xs, mx); fe[4] = stdev(ys, my); fe[5] = stdev(zs, mz);
    fe[6] = stdev(mag, mm);
    fe[7] = diff / (n - 1);
}
```

### test_features.cpp（PC で動かす）

```cpp
// PC でテストする: g++ -std=c++17 -Wall test_features.cpp -o test_features && ./test_features
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include "features.h"
#include "model.h"

bool near(float a, float b) { return std::fabs(a - b) < 1e-4f; }

int main() {
    constexpr int N = 50;
    float xs[N], ys[N], zs[N], fe[8];

    // 1. 止まっている（z だけ 1g）→ ばらつきは 0、判定は rest
    for (int i = 0; i < N; i++) { xs[i] = 0; ys[i] = 0; zs[i] = 1; }
    features(xs, ys, zs, N, fe);
    assert(near(fe[2], 1.0f));
    assert(near(fe[6], 0.0f));
    assert(std::strcmp(predict(fe), "rest") == 0);

    // 2. 大きく揺れている → ばらつきが大きい
    for (int i = 0; i < N; i++) zs[i] = (i % 2) ? 1.5f : 0.5f;
    features(xs, ys, zs, N, fe);
    assert(fe[6] > 0.4f);
    assert(fe[7] > 0.9f);

    printf("テストはすべて通りました\n");
}
```

```bash
cd ~/apps/pico-cpp
g++ -std=c++17 -Wall test_features.cpp -o test_features && ./test_features
```

- `assert(条件)` は、条件が正しくなければそこで止まり、何行目かを表示します
- 判定の結果（`rest` など）は、学習したデータによって変わります。自分の `model.h` に合わせて、テストを書き直してください
- **PC で集めた CSV（10章の features.csv）を読んで、PC の Python と C++ で同じ判定になるか**を確かめるテストも書いておくと、`features()` の計算のまちがいに気付けます

### collar.cpp（ピコ用）

ピコ用のファイルは、センサーを読んで、テスト済みの関数を呼ぶだけにします。

```cpp
#include "features.h"
#include "model.h"
#include "mpu6050.h"
// ……
read_window(xs, ys, zs);              // センサー（ピコに頼る部分）
features(xs, ys, zs, N, fe);          // 計算（PC でテスト済み）
const char* label = predict(fe);      // 判定（PC でテスト済み）
```

## プログラムに名前とバージョンを入れる

現場から戻ってきたピコに、どのバージョンのプログラムが入っているかわかるように、名前とバージョンをプログラムに入れておきます。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "pico/binary_info.h"

#define APP_VERSION "1.2.0"

// picotool info で読める情報
bi_decl(bi_program_name("cow-collar"));
bi_decl(bi_program_version_string(APP_VERSION));
bi_decl(bi_program_description("牛の首輪: 行動を判定して1分ごとに送る"));

int main() {
    stdio_init_all();
    sleep_ms(1500);
    printf("cow-collar %s（ビルド %s %s）\n", APP_VERSION, __DATE__, __TIME__);
    while (true) sleep_ms(1000);
}
```

- 起動したときに `printf` でバージョンを出しておくと、出力を見るだけでわかります。`__DATE__` と `__TIME__` はビルドした日時です
- 書き込みモードのピコなら、`picotool info -a` で名前・バージョン・ビルドした日時が読めます（2章）
- バージョンは「大きな変更.機能の追加.まちがいの修正」の3つの数で付けるのが一般的です
- ソースコードは git で管理し、バージョンを付けたときに `git tag v1.2.0` で印を付けておくと、あとから同じプログラムをビルドし直せます

## 1行ずつ止めて調べる（デバッグ）

`printf` だけではわからないまちがいは、**Debug Probe**（Raspberry Pi の公式の道具）と **gdb** で、プログラムを途中で止めて、変数の値を見ながら調べます。

### つなぎ方

| Debug Probe | ピコ |
| --- | --- |
| D（SWD）の3本の線 | ピコの下の端の **DEBUG** の3本のピン（SWCLK・GND・SWDIO） |
| USB | PC |

ピコの DEBUG のピンには、ピンヘッダのはんだ付けが必要です（Pico H は最初から付いている）。

### 使い方

```bash
sudo apt install openocd gdb-multiarch
cd ~/apps/pico-cpp
cmake -S . -B build-debug -DCMAKE_BUILD_TYPE=Debug
make -C build-debug -j4 blink
```

ターミナルを2つ開きます。1つ目で openocd を動かします（Pico 2 は `rp2040.cfg` を `rp2350.cfg` にします）。

```bash
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg -c "adapter speed 5000"
```

2つ目で gdb を動かします。

```bash
gdb-multiarch build-debug/blink.elf
```

gdb の中で、次のように打ちます。

```text
(gdb) target remote localhost:3333
(gdb) load
(gdb) monitor reset init
(gdb) break main
(gdb) continue
(gdb) next
(gdb) print total
```

| gdb のコマンド | 意味 |
| --- | --- |
| `load` | プログラムを書き込む（BOOT を押さなくてよい） |
| `break main` | `main` に来たら止める。`break blink.cpp:20` なら20行目 |
| `continue` | 次に止まるところまで進める |
| `next` / `step` | 1行進める（`step` は関数の中に入る） |
| `print 変数` | 変数の値を見る |
| `backtrace` | 今どの関数の中にいるか（止まったときの場所を調べる） |

VS Code の拡張機能「Raspberry Pi Pico」を使うと、同じことを画面のボタンでできます（19章）。
くわしくは [Getting started with Raspberry Pi Pico-series](https://datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf) のデバッグの章を見てください。

> Debug Probe がないときは、もう1台のピコを Debug Probe として使うこともできます（[debugprobe](https://github.com/raspberrypi/debugprobe)）。

## たくさんのピコに書き込む

### .uf2 をコピーする

一番簡単なのは、1台ずつ書き込みモードにして、同じ `.uf2` をコピーする方法です。次のスクリプトは、書き込みモードのピコがつながるのを待って、つながったら書き込みます。

```bash
#!/bin/sh
# 使い方: sh flash_many.sh build/collar.uf2
# BOOT を押しながら1台ずつつなぐ。Ctrl+C で終わり
n=0
while true; do
    echo "書き込みモードのピコを待っています..."
    while [ ! -d /run/media/$USER/RPI-RP2 ]; do sleep 0.5; done
    cp "$1" /run/media/$USER/RPI-RP2/ && sync
    n=$((n + 1))
    echo "$n 台目を書き込みました。抜いて、次のピコをつないでください"
    while [ -d /run/media/$USER/RPI-RP2 ]; do sleep 0.5; done
done
```

### picotool で書き込んで確かめる

picotool を使うと、書き込んだあとに中身を確かめ（`-v`）、動かす（`-x`）までを1行でできます。

```bash
picotool load -v -x build/collar.uf2
picotool info -a        # 書き込みモードで、名前とバージョンを確かめる
```

### 1台ずつの番号

ピコのフラッシュのチップには、1台ずつ違う番号（ユニーク ID）が入っています。データを送るときに、どのピコからかを見分けるのに使えます。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"
#include "pico/unique_id.h"

int main() {
    stdio_init_all();
    sleep_ms(1500);
    char id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    pico_get_unique_board_id_string(id, sizeof(id));
    printf("このピコの番号: %s\n", id);
    while (true) sleep_ms(1000);
}
```

牛の番号のように、人が決める番号は、17章の方法でフラッシュに保存します。工場で書き込むときに、ユニーク ID と牛の番号の対応表を作っておくと管理しやすくなります。

## 現場で困らないための工夫

| 工夫 | 方法 |
| --- | --- |
| 止まったら自動で再起動 | ウォッチドッグ（17章） |
| 何が起きたか後で調べられる | 再起動の回数・理由、センサーのエラーの回数をフラッシュに残す（17章） |
| センサーが壊れても止まらない | 戻り値を確かめ、読めないときは前の値を使うか、エラーとして送る（15章） |
| 電池が減ったときに慌てない | VSYS を測り、低くなったら送る回数を減らして、知らせる（17章） |
| 状態が外からわかる | LED の点滅のしかたで状態を表す（例: 1回 = 正常、2回 = センサーのエラー、3回 = 電池が少ない） |
| プログラムを入れ替えられる | USB の端子をケースの外から使えるようにしておく。書き込みモードにするボタンも |
| 設定を1台ずつ変えられる | 設定はコードに書かず、フラッシュに保存（17章）。USB から変えられるようにする |

## 知っておくこと

### プログラムの読み出し

RP2040（Pico、Pico W）は、フラッシュの中身を読み出すことができます。プログラムを読まれたくないときは、RP2350（Pico 2）のセキュアブートなどの機能を検討します。

### ライセンス

Pico SDK は **BSD-3-Clause** というライセンスで公開されています。製品に使うことはできますが、製品の説明書などに、著作権の表示とライセンスの文を載せる必要があります。USB のライブラリ（TinyUSB）など、SDK が中で使っているライブラリにも、それぞれのライセンスがあります。
使ったライブラリと、そのライセンスの一覧を作っておきましょう。

### 無線の認証

Pico W などで無線を使う製品を日本で使うには、使う無線のモジュールが技術基準適合証明（技適）を受けている必要があります。
自分で作った基板に無線のモジュールを載せるときは、そのモジュールが技適を受けているか、販売元の情報で確かめます。

## 出荷前のチェックリスト

- [ ] PC のテストが全部通る
- [ ] プログラムの名前とバージョンが入っていて、起動したときに表示される
- [ ] ソースコードに、そのバージョンの印（git のタグ）を付けた
- [ ] ウォッチドッグが入っていて、わざと止めたときに再起動することを確かめた
- [ ] センサーを外したとき・壊れたときに、止まらずにエラーを知らせることを確かめた
- [ ] 電池で決めた期間動くことを、電流を測って計算した（13章・17章）
- [ ] 何日も続けて動かして、止まらないことを確かめた
- [ ] 設定がフラッシュに保存され、電源を切っても残ることを確かめた
- [ ] 書き込みの手順を書いた。別の人がその手順で書き込めた
- [ ] 使ったライブラリのライセンスの一覧を作った

## まとめ

- 計算（特徴量・判定）とピコに頼る部分を分けて、計算は PC でテストする
- `bi_decl` で名前とバージョンを入れ、起動時にも表示する。git のタグと合わせる
- 難しいまちがいは Debug Probe と gdb で、止めて調べる
- 量産の書き込みは、`.uf2` のコピーか `picotool load -v -x` をスクリプトにする
- 1台ずつの番号はユニーク ID、人が決める番号はフラッシュに
- ウォッチドッグ、エラーの記録、LED での表示で、現場で困らないようにする
