# 3. VS Code でプロジェクトを作って動かす

## この章でわかること

- VS Code の拡張機能で開発するときのしくみ
- 新しいプロジェクトの作り方と、できるファイルの意味
- 書く → ビルド → 書き込む → 出力を見る、の流れ
- 最初のプログラム（Lチカ）を動かすまで

2章の開発環境ができている前提です。この章のとおりに進めると、ボードの LED が点滅し、VS Code に `printf` の出力が出ます。

## しくみ

![VS Code で C++ を開発するときのしくみ](images/vscode-system.svg)

- **プロジェクト**は1つのフォルダで、1つのプログラムになります（例: `~/apps/collar` → `collar.uf2`）
- 拡張機能は、`~/.pico-sdk` の SDK・コンパイラ・CMake を使ってビルドし、picotool で USB からピコに書き込みます
- Debug Probe があれば、SWD という線から書き込んだり、行で止めて調べたりできます（4章）



## 開発の流れ

![VS Code での開発の流れ](images/vscode-flow.svg)

①（2章）と②は最初だけです。ふだんは「③書く → ④ビルド → ⑤書き込む → ⑥出力を見る」をくり返します。

## ② 新しいプロジェクトを作る

左のピコのアイコンを押して、Quick Access の **New C/C++ Project** を押すと、プロジェクトを作る画面が開きます。

![New C/C++ Project の画面（イメージ）](images/vscode-new-project.svg)

| 番号 | 項目 | 選ぶもの |
| --- | --- | --- |
| ① | Name | プロジェクトの名前（例: `blink`）。フォルダとプログラムの名前になる。英数字と `_` だけにする |
| ② | Board type | ボードの種類。公式ピコなら **Pico**、Pico 2 なら **Pico 2**、Pico W なら **Pico W** |
| ③ | Location | 作る場所。**`/home/ユーザー名/apps`** を選ぶと、`~/apps/blink` ができる |
| ④ | Pico SDK version | SDK のバージョン。いちばん新しいものでよい |
| ⑤ | Features | 使う機能（SPI、I2C、UART、PIO、DMA、HW watchdog、HW timer、HW clocks など）。選ぶと `CMakeLists.txt` にライブラリが足され、使い方の例のコードも入る。あとから足すこともできる |
| ⑥ | Stdio support | **Console over USB に ☑**。`printf` が USB で PC に届く。Console over UART の ☑ は外してよい |
| ⑦ | Code generation options | **Generate C++ code に ☑**（`.cpp` ができる）。Enable C++ exceptions と RTTI は ☐ のまま（11章） |
| ⑧ | Debugger | Debug Probe を使うなら **DebugProbe (CMSIS-DAP)**（そのままでよい） |

最後に **Create** を押します。VS Code が、できたプロジェクトのフォルダを開き直します。

- **初めてのときは、`~/.pico-sdk` に SDK やコンパイラをダウンロードするので、数分かかります**（右下に進み具合が出ます）
- **⑥の Console over USB はとても大事です。** USB の出力がないプログラムを書き込むと、次の書き込みのときに、BOOT ボタンを押す必要があります
- 項目の名前や並びは、拡張機能のバージョンで少し違うことがあります（この図は 0.23.0 のもの）

### できるファイル

```text
~/apps/blink/
├── CMakeLists.txt          ビルドの設定（下で説明）
├── blink.cpp               自分のプログラム。ここに書く
├── pico_sdk_import.cmake   SDK を読み込む
├── .vscode/                拡張機能の設定（ふつうは触らない）
│   ├── settings.json
│   ├── tasks.json          Compile や Run の中身
│   ├── launch.json         デバッグの設定
│   └── c_cpp_properties.json   補完の設定
└── build/                  ビルドしてできたもの（blink.uf2 など）
```

`CMakeLists.txt` の中心は、次の部分です。

```cmake
# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
# （SDK のバージョンと場所を決める行。消したり書き換えたりしない）
# ……

add_executable(blink blink.cpp)

pico_enable_stdio_uart(blink 0)
pico_enable_stdio_usb(blink 1)

target_link_libraries(blink
        pico_stdlib)
```

| 行 | 意味 |
| --- | --- |
| `DO NOT EDIT` の部分 | 拡張機能が SDK・コンパイラの場所を決める。触らない |
| `add_executable(blink blink.cpp)` | `blink.cpp` から `blink` というプログラムを作る |
| `pico_enable_stdio_usb(blink 1)` | `printf` を USB で PC に送る |
| `target_link_libraries(blink pico_stdlib)` | 使うライブラリ。I2C を使うなら `hardware_i2c` を足す（4章の表） |

## ③ 書く（Lチカ）

`blink.cpp` を開いて、中身を全部消し、次のプログラムを貼り付けます。ボードの LED（GP25）を点滅させ、そのたびに `printf` で知らせます。

```cpp run
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint LED_PIN = 25;      // 公式ピコの LED は GP25

int main() {
    stdio_init_all();             // printf を USB で送れるようにする
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    bool on = false;
    while (true) {
        on = !on;
        gpio_put(LED_PIN, on);
        printf("LED %s\n", on ? "ON" : "OFF");
        sleep_ms(500);
    }
}
```

中身の意味は6章で説明します。

- 関数名を打ち始めると、候補が出ます（補完）。`gpio_` まで打つと、GPIO の関数の一覧が出ます
- まちがいがあると、**ビルドする前に**赤い波線が出ます

> Pico W のときは、LED の点け方が違います（6章）。

## ④ ビルドする

Quick Access の **Compile Project** を押します（下のバーの **Compile** でも同じ）。
下の「ターミナル」に進み具合が出て、最後に `build/blink.uf2` ができます。

- 1回目は SDK 全体をビルドするので、1〜2分かかります。2回目からは変えたところだけなので、数秒です
- エラーは「問題」の欄（Ctrl + Shift + M）にも一覧で出て、クリックするとその行に飛びます。エラーの読み方は付録B

## ⑤ 書き込む

ピコを USB でつないで、Quick Access の **Run Project (USB)** を押します（下のバーの **Run** でも同じ）。
picotool がピコを書き込みモードにして書き込み、ピコが再起動してプログラムが動き出します。ボードの LED が点滅すれば成功です。

**ピコで今なにが動いているか**で、BOOT ボタンが要るかどうかが変わります。

| ピコで動いているもの | Run Project (USB) で |
| --- | --- |
| C++ のプログラム（Console over USB あり） | そのまま書き込める。BOOT は要らない |
| 書き込みモード（`RPI-RP2` が見えている） | そのまま書き込める |
| MicroPython（買ったときや、付録E で使ったあと） | 自動で書き込みモードにできない。**BOOT を押しながら USB をつないでから** Run を押す |
| USB を使わない C++ のプログラム | 同じく、BOOT を押しながらつないでから Run を押す |

何が動いているかは、Pico Studio の「接続の確認」（5章）でわかります。

> 「デバイスが見つからない」「権限がない（LIBUSB_ERROR_ACCESS）」と出たら、2章の手順3の udev ルールを入れて、ピコを抜き差しします。

## ⑥ 出力を見る

`printf` の出力は、次のどちらかで見ます。

**VS Code の Serial Monitor**（拡張機能 Serial Monitor が必要。2章）

1. 下の欄の **SERIAL MONITOR** タブを開く（なければ、表示 → ターミナルを開いてから探す）
2. Port で `/dev/ttyACM0`、Baud rate で `115200` を選ぶ
3. **Start Monitoring** を押す → `LED ON` / `LED OFF` が流れる

**Pico Studio**（5章）

1. ポートを選んで「接続」を押す → 出力欄に `LED ON` / `LED OFF` が流れる

> **ポートは1つのソフトでしか使えません。** 書き込む前に、Serial Monitor は **Stop Monitoring**、Pico Studio は「切断」を押します。開いたままだと、書き込みのあとにつながらないことがあります。

## プログラムを直して、もう一度

`sleep_ms(500)` を `sleep_ms(100)` に変えて、保存（Ctrl + S）→ Compile → Run と進めると、LED が速く点滅します。
これが、ふだんの開発のくり返しです。

### 6章から先のコードを試すとき

- 新しくプロジェクトを作るか、今のプロジェクトの `.cpp` の中身を置き換えて試します
- I2C などを使うコードは、`target_link_libraries` にライブラリを足します（4章の表）
- 9章の `mpu6050.h` など、Pico Studio に入っているヘッダーを使うときは、プロジェクトのフォルダにコピーします

```bash
cp ~/apps/pico-studio/cpp/include/*.h ~/apps/blink/
```

## まとめ

- **New C/C++ Project** で、場所を `~/apps`、Console over USB と Generate C++ code に ☑ して作る
- ふだんは「書く → Compile → Run (USB) → Serial Monitor」のくり返し
- MicroPython が動いているピコや、USB を使わないプログラムのときは、BOOT を押しながらつないでから Run
- ポートは1つのソフトでしか使えない。書き込む前に Serial Monitor や Pico Studio を止める
