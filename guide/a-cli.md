# 付録A. コマンドで操作する

## この付録でわかること

- VS Code を使わず、ターミナルのコマンドだけで C++ のプログラムをビルドして書き込む方法
- コマンド用の道具の入れ方（`setup-sdk.sh` がすること）
- 1つのフォルダに、いくつものプログラムを置いてビルドする方法
- 書き込みモードへの切り替え・書き込み・出力を見る・ピコの中を調べるコマンド
- 手順をスクリプトにまとめる方法

ふだんの開発は VS Code で行います（3章）。この付録は、次のようなときに使います。

- 手順をスクリプトにまとめたい（量産の書き込みなど。17章）
- VS Code の中で何が起きているかを知りたい
- 小さなプログラムを、いくつも1つのフォルダでまとめて試したい

コマンドの中の単語（`cmake` や `make` など）をクリックすると、その意味が吹き出しで出ます。

## コマンド用の道具を入れる

VS Code の拡張機能が入れる道具（`~/.pico-sdk`）は、VS Code の中から使うためのものです。ターミナルで直接ビルドしたいときは、次のスクリプトで、コマンド用の道具をまとめて入れます。途中でパスワードを聞かれます。

```bash
sh ~/apps/pico-studio/cpp/setup-sdk.sh
```

最後に `OK: C++ を開発できます` と出れば完了です。ターミナルを開き直してから使います。何回打っても大丈夫です（あるものはそのまま使い、足りないものだけを足します）。

### このスクリプトがすること

スクリプトは、上から順に次の5つを行います。中身は `~/apps/pico-studio/cpp/setup-sdk.sh` で読めます。

| 順番 | すること | 入る場所 | 中身 |
| --- | --- | --- | --- |
| 1/5 | コンパイラなどを入れる（`sudo apt install`） | `/usr/bin` など（PC 全体） | 下の「1. コンパイラなどを入れる」の表のパッケージ |
| 2/5 | Pico SDK 2.1.1 をダウンロードする（`git clone` と `git submodule update --init`） | `~/pico/pico-sdk` | SDK 本体と、SDK が使うライブラリ（下の表） |
| 3/5 | SDK の場所を登録する | `~/.bashrc` の最後に1行 | `export PICO_SDK_PATH=/home/ユーザー名/pico/pico-sdk` |
| 4/5 | プロジェクトのフォルダを用意して、そろったか確かめる | `~/apps/pico-cpp` | `CMakeLists.txt`、`pico_sdk_import.cmake`、`.gitignore`、`blink.cpp`、`mpu6050.h`、`ws2812.h` |
| 5/5 | picotool を作って入れる（`git clone` してビルド）。sudo なしで使えるように udev ルールも入れる | `~/pico/picotool`（ソース）、`~/.local/bin/picotool`、`/etc/udev/rules.d/60-picotool.rules` | USB でピコを書き込みモードにする・書き込む・中を調べるツール（この付録・17章）。なくてもビルドはできる |

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
| `python3` | SDK のビルドの途中で使う |
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

> VS Code を使っているなら、拡張機能の **Raspberry Pi Pico** で、準備・ビルド・書き込み・デバッグをボタンでできます（3章）。
> この付録では、何が起きているかわかるように、コマンドで進めます。

## プロジェクトのフォルダ

### フォルダを作る

```bash
python3 ~/apps/pico-studio/devenv.py init
```

`~/apps/pico-cpp` に、ビルドに必要なファイルができます（「まとめて入れる」のスクリプトを使った人は、もうできています）。
すでにあるファイルは上書きしないので、何回打っても大丈夫です。別のフォルダに作るときは `init ~/apps/collar` のようにフォルダを書きます。

```text
~/apps/pico-cpp/
├── CMakeLists.txt          ビルドの設定（下で説明）
├── pico_sdk_import.cmake   SDK を読み込む（SDK からコピーしたもの）
├── .gitignore              git で build フォルダを管理しないための設定
├── blink.cpp               Lチカ（最初のプログラム）
├── mpu6050.h               MPU-6050 を読むクラス（9章）
├── ws2812.h                RGB LED を光らせるクラス（6章）
└── build/                  ビルドしてできたファイル（.uf2 など）。cmake を打つとできる
```

`setup-sdk.sh` を使った人は、もうできています。

### CMakeLists.txt

ビルドの設定です。**このフォルダの `.cpp` が、1つずつプログラムになります**（`blink.cpp` → `build/blink.uf2`）。
6〜15章の C++ のコードは、`.cpp` として保存すれば、どれもそのままビルドできます。中心の部分は次のとおりです。

```cmake
cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)        # pico_sdk_init より前に読む
project(pico_cpp C CXX ASM)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

set(PICO_LIBS pico_stdlib hardware_adc hardware_i2c ...)   # 使うライブラリ（4章の表のもの）

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

- `test_` で始まる `.cpp` は、PC 用のテスト（17章）なので、ピコ用にはビルドしません
- 1つのプログラムを複数の `.cpp` に分けたいとき（11章）は、`add_executable(collar collar.cpp sensor.cpp)` のように、自分で行を書き足します

## 全体の流れ

| 順番 | やること | コマンド | VS Code では |
| --- | --- | --- | --- |
| 0 | 道具とプロジェクトを用意する（最初の1回だけ） | `sh ~/apps/pico-studio/cpp/setup-sdk.sh` | 拡張機能が自動で入れる |
| 1 | USB で認識しているか確かめる | `lsusb -d 2e8a:` | （Pico Studio の「USB で認識」） |
| 2 | ビルドの準備（最初と、CMakeLists.txt を変えたとき） | `cmake -S . -B build` | （自動） |
| 3 | ビルドする | `make -C build -j4 blink` | Compile Project |
| 4 | 書き込みモードにする | MicroPython なら `mpremote bootloader`、C++ なら `picotool reboot -f -u` | （自動） |
| 5 | 書き込む | `cp build/blink.uf2 /run/media/$USER/RPI-RP2/` | Run Project (USB) |
| 6 | 出力を見る | `python3 -m serial.tools.miniterm /dev/ttyACM0 115200` | Serial Monitor |
| 7 | ピコの中のプログラムを調べる（必要なとき） | `picotool info -a` | （なし） |

> **ポートは1つのソフトでしか使えません。** コマンドを使う前に、Pico Studio の「切断」や、VS Code の Serial Monitor の Stop Monitoring を押してください。

## 手順1: USB で認識しているか確かめる

```bash
lsusb -d 2e8a:
```

| 結果 | 状態 |
| --- | --- |
| `2e8a:000a Raspberry Pi Pico` | C++（Pico SDK）のプログラムが USB の出力つきで動いている |
| `2e8a:0005 MicroPython Board in FS mode` | MicroPython で動いている |
| `2e8a:0003 Raspberry Pi RP2 Boot`（Pico 2 は `2e8a:000f`） | 書き込みモード（BOOTSEL） |
| 何も出ない | 認識されていない。または USB を使わないプログラムが動いている |

## 手順2〜3: ビルドする

プロジェクトのフォルダ（`~/apps/pico-cpp`）で行います。このフォルダの `.cpp` が、1つずつプログラムになります（`blink.cpp` → `build/blink.uf2`）。
`cd` で「そのようなファイルやディレクトリはありません」と出たら、フォルダがまだありません。`python3 ~/apps/pico-studio/devenv.py init` で作ります。

```bash
cd ~/apps/pico-cpp
cmake -S . -B build
make -C build -j4 blink
```

- `cmake -S . -B build` は、今のフォルダの `CMakeLists.txt` を読んで、`build` フォルダにビルドの手順を作ります。最初と、`.cpp` を足したり消したりしたときに打ちます
- `make -C build -j4 blink` は、`build` フォルダで `blink` をビルドします。`build/blink.uf2` ができます
- エラーは `blink.cpp:12:5: error: ...` のように出ます。12行目の5文字目という意味です

## 手順4: 書き込みモードにする

**ピコで今なにが動いているかで、方法が違います。** 手順1の `lsusb -d 2e8a:` で確かめます。

| `lsusb` の表示 | 動いているもの | 書き込みモードにするコマンド |
| --- | --- | --- |
| `2e8a:0005 MicroPython Board` | MicroPython | `mpremote bootloader` |
| `2e8a:000a Raspberry Pi Pico` | C++ のプログラム（`stdio_init_all()` あり） | `picotool reboot -f -u`、または下の 1200 bps の方法 |
| `2e8a:0003`（Pico 2 は `000f`） | もう書き込みモード | 何もしなくてよい |
| 何も出ない | USB を使わないプログラム、または止まっている | BOOT を押しながら USB をつなぎ直す |

**初めて C++ を書き込むとき**は、まだ MicroPython が動いているので、`mpremote bootloader` を使います。

```bash
mpremote bootloader
```

C++ のプログラムが動いているときは、picotool を使います。

```bash
picotool reboot -f -u
```

picotool がないときは、ポートを 1200 bps で開いて閉じます。Pico SDK のプログラムは、これを「書き込みモードにして」という合図として受け取ります。

```bash
python3 -c "import serial; serial.Serial('/dev/ttyACM0', 1200).close()"
```

`RPI-RP2` のドライブが出てくれば成功です。うまくいかないときは、BOOT を押しながら USB をつなぎ直します。

> `picotool` が「見つかりません」と出るときは、`sh ~/apps/pico-studio/cpp/setup-sdk.sh` を打ち直すと入ります（この付録の最初）。VS Code の拡張機能が入れた `~/.pico-sdk/picotool/…/picotool` も使えます。ビルドの途中で `build/_deps` にできる picotool は、USB の機能なしで作られているので、ピコの操作には使えません。

## 手順5: 書き込む

```bash
cp build/blink.uf2 /run/media/$USER/RPI-RP2/
```

コピーが終わると、ピコが自動で再起動して、プログラムが動き始めます。

> ドライブの場所は PC によって違います。`/run/media/$USER/` に見つからないときは、`/media/$USER/` を見てください。
> Pico 2 のドライブ名は `RP2350` です。

picotool を使うと、書き込みモードへの切り替えから書き込みまでを1行でできます。

```bash
picotool load -x -f build/blink.uf2
```

## 手順6: 出力を見る

```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200
```

- 止めるときは **Ctrl + ]** です
- 書き込み直すとポートが一度消えるので、miniterm を止めてからつなぎ直します
- 送った文字は、ピコの `getchar()` などで受け取れます

## 手順7: ピコの中のプログラムを調べる

picotool で、書き込まれているプログラムの名前・ビルドした日時・使っているピンなどを見られます（書き込みモードのとき）。

```bash
picotool info -a
```

プログラムに名前やバージョンを入れる方法は17章にあります。

## 手順をスクリプトにする

ビルドから出力を見るまでを、1つのスクリプトにまとめておくと楽です。次の内容を `~/apps/pico-cpp/run.sh` として保存します。

```bash
#!/bin/sh
# 使い方: sh run.sh blink
set -e
cd "$(dirname "$0")"
make -C build -j4 "$1"
python3 -c "import serial; serial.Serial('/dev/ttyACM0', 1200).close()" 2>/dev/null || true
echo "書き込みモードを待っています..."
while [ ! -d /run/media/$USER/RPI-RP2 ]; do sleep 0.5; done
cp "build/$1.uf2" /run/media/$USER/RPI-RP2/
echo "書き込みました。出力を表示します（Ctrl+] で終わり）"
sleep 3
python3 -m serial.tools.miniterm /dev/ttyACM0 115200
```

```bash
sh run.sh blink
```

## VS Code のプロジェクトをコマンドでビルドする

VS Code で作ったプロジェクト（3章）も、同じコマンドでビルドできます。`CMakeLists.txt` の `DO NOT EDIT` の部分が、`~/.pico-sdk` の SDK とコンパイラを選ぶためです。

```bash
cd ~/apps/blink
cmake -S . -B build
make -C build -j4
```

うまくいかないときは、VS Code の Compile Project を使います。

## 困ったとき（コマンド）



## まとめ

- コマンド用の道具は `setup-sdk.sh` でまとめて入れる。中身はこの付録の表のとおり
- `~/apps/pico-cpp` は、フォルダの `.cpp` が1つずつプログラムになる。`.cpp` を足したら `cmake -S . -B build` を打ち直す
- ビルドは `make -C build -j4 名前`、書き込みは `.uf2` を `RPI-RP2` にコピーするか `picotool load -x -f`
- 書き込みモードには、MicroPython なら `mpremote bootloader`、C++ なら `picotool reboot -f -u`
- 出力は miniterm で見る。止めるのは Ctrl + ]
