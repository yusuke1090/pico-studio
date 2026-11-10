# 2. コマンドで操作する

<!-- python -->

## この章でわかること

- Pico Studio を使わず、ターミナルのコマンドだけでピコを操作する方法
- 接続の確認から実行・保存まで、どの順番で何を打てばよいか
- Pico Studio のボタンと、コマンドの対応

コマンドの操作には **mpremote** を使います。MicroPython の公式ツールです。

コマンドの中の単語（`sudo` や `apt` など）をクリックすると、その意味が吹き出しで出ます。

ラズパイや Jetson に ssh で実装した経験があるなら、12章の対応表も役に立ちます。

## 全体の流れ

上から順に進めます。2回目からは手順2から始めて、MicroPython が入っていれば手順3は飛ばします。

| 順番 | やること | コマンド |
| --- | --- | --- |
| 1 | mpremote を入れる（最初の1回だけ） | `pipx install mpremote` |
| 2 | USB で認識しているか確かめる | `lsusb -d 2e8a:` |
| 3 | MicroPython を書き込む（BOOTSEL モードのときだけ） | `cp RPI_PICO-*.uf2 /run/media/$USER/RPI-RP2/` |
| 4 | シリアルポートを確かめる | `ls -l /dev/ttyACM0` |
| 5 | MicroPython の応答を確かめる | `mpremote exec "import os; print(os.uname())"` |
| 6 | コードを実行する | `mpremote run hello.py` |
| 7 | 実行を止める | Ctrl + C のあと `mpremote soft-reset` |
| 8 | ピコに保存する | `mpremote cp hello.py :hello.py` |
| 9 | 保存したファイルを確認する | `mpremote ls` |
| 10 | REPL で1行ずつ試す（必要なとき） | `mpremote repl` |
| 11 | ピコを再起動する（必要なとき） | `mpremote reset` |

> **Pico Studio と同時には使えません。** 1つのポートを2つのソフトで使うと、やり取りが混ざって動かなくなります。
> コマンドを使う前に、Pico Studio で「切断」を押してください。

## 手順1: mpremote を入れる

最初の1回だけです。パスワードを聞かれたら打って Enter を押します。

```bash
sudo apt install pipx
pipx install mpremote
pipx ensurepath
```

打ち終わったらターミナルを開き直して、次のコマンドでバージョンが出れば成功です。

```bash
mpremote version
```

## 手順2: USB で認識しているか確かめる

「接続の確認」の **USB で認識** にあたります。ピコをつないで、次を打ちます。

```bash
lsusb -d 2e8a:
```

| 結果 | 状態 | 次にやること |
| --- | --- | --- |
| `2e8a:0005 MicroPython Board in FS mode` | MicroPython で動いている | 手順4へ |
| `2e8a:0003 Raspberry Pi RP2 Boot`（Pico 2 は `2e8a:000f`） | 書き込みモード（BOOTSEL） | 手順3へ |
| 何も出ない | 認識されていない | ケーブルと USB ポートを確かめる（11章） |

## 手順3: MicroPython を書き込む

手順2で BOOTSEL モードだったときだけ行います。「最新の MicroPython を書き込む」ボタンにあたります。

1. [MicroPython のダウンロードページ](https://micropython.org/download/RPI_PICO/) から `.uf2` ファイルをダウンロードする（Pico 2 は [こちら](https://micropython.org/download/RPI_PICO2/)）
2. ピコのドライブにコピーする

```bash
cp ~/ダウンロード/RPI_PICO-*.uf2 /run/media/$USER/RPI-RP2/
```

コピーが終わると、ピコは自動で再起動します。

> ドライブの場所は PC によって違います。`/run/media/$USER/` に見つからないときは、`/media/$USER/` を見てください。
> Pico 2 のドライブ名は `RP2350` です。

## 手順4: シリアルポートを確かめる

「接続の確認」の **シリアル接続** にあたります。mpremote は、コマンドを打つたびに自動でつないで、終わると切ります。「接続」ボタンにあたる操作はありません。

```bash
ls -l /dev/ttyACM0
```

```text
crw-rw----+ 1 root dialout 166, 0 Nov  6 12:34 /dev/ttyACM0
```

- `crw-rw----+` のように最後に **`+`** が付いていれば、権限の設定もできています
- `+` がないときは、下の「`+` がないとき」の設定をします
- ファイルが見つからないときは、手順2に戻ります

### `+` がないとき

ログイン中のユーザーがピコのポートを使えるように、設定ファイルを作ります。最初の1回だけです。

```bash
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/70-pico-studio.rules
sudo rm -f /etc/udev/rules.d/99-pico-studio.rules
sudo udevadm control --reload-rules
```

| 行 | やっていること |
| --- | --- |
| 1行目 | 設定ファイルを作る。メーカー番号 `2e8a` のシリアルポートを、ログイン中のユーザーが使えるようにする |
| 2行目 | 古い設定ファイルがあれば消す（番号が大きすぎて効かないため） |
| 3行目 | 設定を読み直す |

打ち終わったら、**ピコを一度抜いて、つなぎ直します**。もう一度 `ls -l /dev/ttyACM0` を打って、`+` が付いていれば成功です。

### ポートの名前を調べる

ポートの名前は、次のコマンドで調べられます。

```bash
mpremote connect list | grep 2e8a
```

```text
/dev/ttyACM0 334e39323614da8b 2e8a:0005 MicroPython Board in FS mode
```

> ポートを指定しなければ、mpremote はピコを自動で探します。
> ピコを2台以上つないでいるときは、`mpremote connect /dev/ttyACM1 ls` のように先頭で指定します。

## 手順5: MicroPython の応答を確かめる

「接続の確認」の **MicroPython の応答** にあたります。ピコに1行のコードを送って、返事を見ます。

```bash
mpremote exec "import os; print(os.uname())"
```

```text
(sysname='rp2', nodename='rp2', release='1.29.0', version='v1.29.0 on 2026-08-24 (GNU 16.1.0 MinSizeRel)', machine='Raspberry Pi Pico with RP2040')
```

`release` が MicroPython のバージョン、`machine` がボードの名前です。

ストレージの空きは次のコマンドでわかります。

```bash
mpremote df
```

```text
filesystem     size     used    avail use% mounted on
<VfsLfs2>   1441792     8192  1433600    0 /
```

## 手順6: コードを実行する

「▶ 実行」にあたります。PC のテキストエディタでコードを書いて、`hello.py` のように保存しておきます。
保存する場所はどこでも大丈夫です。ここでは `~/apps/pico-code` というフォルダを使います。

```bash
mkdir -p ~/apps/pico-code
cd ~/apps/pico-code
mpremote run hello.py
```

PC にあるファイルをピコへ送って実行します。結果はターミナルに出ます。ピコにファイルは残りません。

> `mpremote run` が読むのは **PC のファイル** で、**ターミナルで今いるフォルダ** が基準です。今いるフォルダは `pwd` でわかります。
> ほかのフォルダにいるときは、`mpremote run ~/apps/pico-code/hello.py` のように場所ごと指定します。

1行だけ試すなら、ファイルを作らずに `exec` が使えます。

```bash
mpremote exec "print(1 + 2)"
```

## 手順7: 実行を止める

「■ 停止」にあたります。ここは Pico Studio と動きが違うので注意してください。

1. ターミナルで **Ctrl + C** を押す
2. 続けて次のコマンドを打つ

```bash
mpremote soft-reset
```

> **Ctrl + C だけでは、ピコのプログラムは止まりません。** 止まるのは、ターミナルへの表示だけです。
> ずっとくり返すプログラムは、ピコの中で動き続けています。`mpremote soft-reset` まで打つと止まります。

## 手順8: ピコに保存する

「ピコに保存」にあたります。

```bash
mpremote cp hello.py :hello.py
```

名前の前の **`:`（コロン）がピコの中** という意味です。`:` がないほうは PC のファイルです。

電源を入れたら自動で動かしたいときは、名前を `main.py` にして保存します。

```bash
mpremote cp hello.py :main.py
```

ピコに保存したファイルは、`run` では動かせません（`run` は PC のファイルを読むため）。動かすときは `exec` で読み込みます。

```bash
mpremote exec "import hello"
```

### おすすめの流れ

プログラムは、次の順番で作ると進めやすくなります。

1. PC のテキストエディタでコードを書く
2. `mpremote run hello.py` で試す（ピコには保存されません）
3. 止めるときは Ctrl + C のあと `mpremote soft-reset`
4. 直して、もう一度試す
5. 完成したら、main.py として保存する
6. ピコを再起動して、自動で動くか確かめる

手順5と6のコマンドは次のとおりです。

```bash
mpremote cp hello.py :main.py
mpremote reset
```

## 手順9: 保存したファイルを確認する

「ピコのファイル」にあたります。

| やること | コマンド |
| --- | --- |
| 一覧を見る | `mpremote ls` |
| 中身を見る | `mpremote cat hello.py` |
| PC に持ち出す | `mpremote cp :log.csv log.csv` |
| 削除する | `mpremote rm hello.py` |

`mpremote ls` は、ファイルの大きさ（バイト）と名前を出します。

```text
ls :
          73 hello.py
```

## 手順10: REPL で1行ずつ試す

出力欄の下の送信欄にあたります。

```bash
mpremote repl
```

```text
Connected to MicroPython at /dev/ttyACM0
Use Ctrl-] or Ctrl-x to exit this shell

>>> 1 + 2
3
```

終わるときは **Ctrl + ]** か **Ctrl + X** を押します。

## 手順11: ピコを再起動する

出力欄の「リセット」にあたります。

```bash
mpremote reset
```

ピコが再起動します。main.py を保存してあれば、そのあと自動で動き始めます。

## 通しでやってみる

ピコをつないでから、コードを実行して保存し、確かめて消すまでの流れです。

```bash
lsusb -d 2e8a:
ls -l /dev/ttyACM0
mpremote exec "import os; print(os.uname())"
mpremote run hello.py
mpremote cp hello.py :hello.py
mpremote ls
mpremote cat hello.py
mpremote rm hello.py
```

## まとめ

- コマンドの操作には mpremote を使う。先に Pico Studio で「切断」を押す
- 確認の順番は、`lsusb`（USB）→ `ls -l /dev/ttyACM0`（シリアル）→ `mpremote exec`（MicroPython）
- 実行は `run`、保存は `cp`。`:` が付いた名前はピコの中のファイル
- Ctrl + C だけではピコのプログラムは止まらない。`mpremote soft-reset` で止める

<!-- /python -->
<!-- cpp -->

## この章でわかること

- Pico Studio を使わず、ターミナルのコマンドだけで C++ のプログラムをビルドして書き込む方法
- どの順番で何を打てばよいか
- Pico Studio のボタンと、コマンドの対応

最初に1回だけ、開発環境（Pico SDK とコンパイラ）と、プロジェクトのフォルダ（`~/apps/pico-cpp`）を用意します。次のコマンドで、まとめて用意できます（くわしくは14章）。

```bash
sh ~/apps/pico-studio/cpp/setup-sdk.sh
```

最後に `OK: C++ でビルドできます` と出たら、ターミナルを開き直してから、下の手順に進みます。
コマンドの中の単語（`cmake` や `make` など）をクリックすると、その意味が吹き出しで出ます。

## 全体の流れ

| 順番 | やること | コマンド | Pico Studio では |
| --- | --- | --- | --- |
| 0 | 開発環境とプロジェクトを用意する（最初の1回だけ） | `sh ~/apps/pico-studio/cpp/setup-sdk.sh` | 接続の確認の「C++ の開発環境」 |
| 1 | USB で認識しているか確かめる | `lsusb -d 2e8a:` | 接続の確認の「USB で認識」 |
| 2 | ビルドの準備（最初と、CMakeLists.txt を変えたとき） | `cmake -S . -B build` | （自動） |
| 3 | ビルドする | `make -C build -j4 blink` | 「▶ ビルドして書き込む」の前半 |
| 4 | 書き込みモードにする | MicroPython なら `mpremote bootloader`、C++ なら `picotool reboot -f -u` | （自動） |
| 5 | 書き込む | `cp build/blink.uf2 /run/media/$USER/RPI-RP2/` | 「▶ ビルドして書き込む」の後半 |
| 6 | 出力を見る | `python3 -m serial.tools.miniterm /dev/ttyACM0 115200` | 出力欄 |
| 7 | ピコの中のプログラムを調べる（必要なとき） | `picotool info -a` | （なし） |

> **Pico Studio と同時には使えません。** 1つのポートを2つのソフトで使うと、やり取りが混ざって動かなくなります。
> コマンドを使う前に、Pico Studio で「切断」を押してください。

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
`cd` で「そのようなファイルやディレクトリはありません」と出たら、フォルダがまだありません。`python3 ~/apps/pico-studio/cpp_build.py init` で作ります。

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

picotool がないときは、ポートを 1200 bps で開いて閉じます。Pico SDK のプログラムは、これを「書き込みモードにして」という合図として受け取ります（Pico Studio もこの方法を使っています）。

```bash
python3 -c "import serial; serial.Serial('/dev/ttyACM0', 1200).close()"
```

`RPI-RP2` のドライブが出てくれば成功です。うまくいかないときは、BOOT を押しながら USB をつなぎ直します。

> `picotool` が「見つかりません」と出るときは、`sh ~/apps/pico-studio/cpp/setup-sdk.sh` を打ち直すと入ります（14章）。ビルドの途中で `build/_deps` にできる picotool は、USB の機能なしで作られているので、ピコの操作には使えません。

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

プログラムに名前やバージョンを入れる方法は18章にあります。

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

## まとめ

- ビルドは `cmake -S . -B build`（最初だけ）と `make -C build blink`
- 書き込みは、書き込みモードのピコに `.uf2` をコピーする。`picotool load -x -f` なら1行
- 書き込みモードには、`picotool reboot -f -u` か、ポートを 1200 bps で開いて閉じる
- 出力は miniterm で見る。止めるのは Ctrl + ]

<!-- /cpp -->
