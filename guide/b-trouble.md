# 11. 困ったとき

## この章でわかること

- つながらないときの調べ方（流れ図）
- 接続・エラー・動作のトラブルと直し方
- PC がピコを認識しているかを、コマンドで確かめる方法
- ピコを初期状態に戻す方法
- 調べるときのコツ

## つながらないとき

まずは次の流れ図にそって確かめてください。

![つながらないときの調べ方](images/trouble-flow.svg)

### 接続のトラブル

| 症状 | 原因と対処 |
| --- | --- |
| 「見つかりません」と出る・ポートが出ない | USB ケーブルが充電専用かもしれない。BOOT ボタンを押しながらつないで「BOOTSEL モード」と出るか確認する |
| 「BOOTSEL モード」は出るがポートは出ない | MicroPython が入っていない。0章・4章の手順で書き込む |
| 「ポートを開く権限がありません」 | 0章の「『ポートを開く権限がありません』と出たとき」の設定をする |
| 「MicroPython の応答がありません」 | Thonny や mpremote、pc_logger.py など、別のソフトが同じポートを使っていないか確認する。プログラムが動いたままなら「■ 停止」か RST |
| 「サーバーに接続できません」（左上） | Pico Studio が止まっている。ターミナルで `./start.sh` を打ち直す |
| ピコが反応しない・固まった | RST ボタンを押して再起動する。だめなら BOOT を押したまま RST を押して書き込みモードにし、MicroPython を入れ直す |
| USR ボタンを押しても反応しない | ボードによってつながっているピンが違う。ボードの説明書や裏面の印字で GP 番号を確かめる |
| 接続してもすぐ切れる | ケーブルや USB ポートを替える。USB ハブを使っているなら PC に直接つなぐ |

![ピコが見つからないとき](images/studio-notfound.png)

## PC がピコを認識しているか、コマンドで確かめる

Pico Studio の「接続の確認」でもわかりますが、ターミナルでも確かめられます。

```bash
lsusb | grep 2e8a       # USB 機器の一覧から、ラズパイ（ID 2e8a）の行を探す
ls /dev/ttyACM*         # シリアルポートを探す
lsblk -o NAME,LABEL | grep RP2   # 書き込みモードのドライブを探す
```

| 結果 | 状態 |
| --- | --- |
| `ID 2e8a:0005 MicroPython Board in FS mode` と出て、`/dev/ttyACM0` がある | **MicroPython で動いている**。Pico Studio で接続できる |
| `ID 2e8a:0003 Raspberry Pi RP2 Boot`（Pico 2 は `2e8a:000f`）と出て、`RPI-RP2`（Pico 2 は `RP2350`）がある | **書き込みモード（BOOTSEL）**。MicroPython を書き込める |
| `2e8a` の行が何も出ない | **認識されていない**。ケーブルが充電専用、差し込みが浅い、USB ポートの不調などを疑う |

`lsusb` は、ピコを抜き差ししながら2回打って、行が増えたり減ったりするかを見るとわかりやすいです。
つないだ瞬間のログは `sudo dmesg -w` で見られます（止めるときは Ctrl+C）。

権限が設定できているかは、`ls -l /dev/ttyACM0` で確かめます。行の最初が `crw-rw----+` のように `+` 付きなら OK です。

## プログラムのエラー

<!-- python -->

エラーが出ると、出力欄に赤い文字で `Traceback` が表示されます。**最後の行**が一番大事です。

![エラーの表示](images/studio-error.png)

エラーの読み方:

```text
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
ZeroDivisionError: division by zero
```

- `line 3` … 3行目でエラーが起きた（コード欄の左の行番号と同じ）
- `ZeroDivisionError` … エラーの種類
- `division by zero` … くわしい説明（この例では「0 で割った」）

### よくあるエラー

| エラー | 意味と対処 |
| --- | --- |
| `SyntaxError: invalid syntax` | 文法のまちがい。`:` の付け忘れ、かっこの閉じ忘れ、全角の記号（`（` `：` など）を探す |
| `IndentationError` | インデント（字下げ）がずれている。スペース4つに揃える |
| `NameError: name 'xxx' isn't defined` | その名前の変数や関数がない。つづりのまちがいか、`import` を忘れていないか |
| `ImportError: no module named 'xxx'` | そのライブラリが MicroPython に入っていない。PC 用のライブラリ（numpy など）はそのままでは使えない。自分で作ったファイルなら、ピコに保存されているか |
| `TypeError` | 型（数・文字など）の組み合わせがおかしい。例: 文字と数を `+` でつないだ → `str(数)` にする |
| `OSError: [Errno 5] EIO` | I2C の通信に失敗した。配線・アドレス・電源を確認し、6章の I2C スキャンをする |
| `OSError: [Errno 110] ETIMEDOUT` | センサーが応答しない。配線を確認、`freq=100000` に下げる |
| `OSError: [Errno 2] ENOENT` | そのファイルがない。ファイル名のつづりと、「ピコのファイル」の一覧を確かめる |
| `MemoryError` | メモリ不足。リストを小さくする、`array` を使う、こまめに保存する（9章） |
| `KeyboardInterrupt` | 「■ 停止」で止めたときに出る。エラーではない |

<!-- /python -->
<!-- cpp -->

C++ では、エラーは2種類あります。

| 種類 | いつわかるか | 例 |
| --- | --- | --- |
| ビルドのエラー | 「▶ ビルドして書き込む」を押したとき。出力欄に赤い文字で出る | `;` の付け忘れ、関数名のまちがい |
| 動いているときのまちがい | 書き込んだあと。**エラーは出ず**、止まったり、おかしな値になったりする | 配列の外を読む、センサーの戻り値を確かめない |

### ビルドのエラーの読み方

```text
main.cpp:12:5: error: 'prinf' was not declared in this scope; did you mean 'printf'?
```

- `main.cpp:12:5` … 12行目の5文字目。**出力欄のこの行をクリックすると、コード欄のその行が選ばれる**
- `error:` … ビルドが止まるまちがい。`warning:`（警告）はビルドは通るが、まちがいのことが多いので直す
- 最後の部分 … くわしい説明。`did you mean` は「もしかして」という意味

エラーがたくさん出たときは、**一番上のエラーから**直します。

### よくあるビルドのエラー

| エラー | 意味と対処 |
| --- | --- |
| `expected ';' before ...` | `;` を付け忘れた。**表示された行の1つ前の行**を見る |
| `'xxx' was not declared in this scope` | その名前がない。つづりのまちがいか、`#include` を忘れていないか |
| `fatal error: xxx.h: No such file or directory` | そのヘッダーがない。自分で作った `.h` なら「PC に保存」したか。コマンドでビルドするなら、`CMakeLists.txt` にライブラリ（`hardware_i2c` など）を足したか |
| `undefined reference to 'xxx'` | 関数の宣言はあるが中身がない。コマンドでビルドするなら、ライブラリ（`pico_multicore` など）を足したか |
| `expected '}' at end of input` | `{` と `}` の数が合っていない |
| `invalid conversion from 'const char*' to 'char*'` | 型が合っていない。`const` を付ける |
| `narrowing conversion` | `{}` で初期化するとき、型が合わない。`static_cast<型>(値)` で変える |
| `region 'RAM' overflowed` | メモリが足りない。大きな配列を小さくする（9章・15章） |
| C++ の開発環境が赤い | Pico SDK かコンパイラがない。14章の「開発環境を用意する」 |

### 書き込んだあとに動きがおかしいとき

| 症状 | 対処 |
| --- | --- |
| 出力欄に何も出ない | `stdio_init_all()` を呼んでいるか。起動直後の出力は消えるので、最初に `sleep_ms(1500)` を入れる |
| 途中で止まる・ピコが反応しない | 配列の外に書いていないか、関数の中に大きな配列を作っていないか（スタックがあふれる。9章）。ウォッチドッグを入れると、止まったときに自動で再起動する（17章） |
| 次の書き込みが自動でできない | 前のプログラムが `stdio_init_all()` を呼んでいないか、止まっている。BOOT を押しながら USB をつなぎ直す |
| センサーの値がずっと 0 | 戻り値を確かめる（`i2c_read_blocking` が負の数ならエラー）。配線と I2C スキャン（6章） |
| 小数の計算が遅い | `double` ではなく `float` を使う。数に `f` を付ける（`3.3f`）。`sqrt` ではなく `sqrtf` |

<!-- /cpp -->

## 動きがおかしい

| 症状 | 対処 |
| --- | --- |
| LED が光らない | ピン番号を確認（公式ピコは 25、Pico W は "LED"、互換ボードは説明書を見る）。外付けなら LED の向き（長い足が＋）と抵抗 |
| センサーの値がずっと 0 や同じ値 | センサーを起こす設定（MPU-6050 なら 0x6B に 0）を忘れていないか |
| 値が大きくふらつく | 配線を短くする、GND を確実につなぐ、平均を取る |
<!-- python -->

| ボタンの値がふらつく | `Pin.PULL_UP` を付け忘れていないか（5章） |

<!-- /python -->
<!-- cpp -->

| ボタンの値がふらつく | `gpio_pull_up` を付け忘れていないか（5章） |

<!-- /cpp -->
| main.py が勝手に動いて操作できない | Pico Studio で接続すると止まる。止まらなければ「■ 停止」、それでもだめなら main.py を削除 |
| 「▶ 実行」が押せない | 未接続か、別のプログラムが実行中。「接続」するか「■ 停止」を押す |
| ガイドが表示されない | 右上の「📘 ガイド」を押す。それでも出なければ、ブラウザで再読み込み（F5） |

## 最後の手段: ピコを初期状態に戻す

ファイルをすべて消して、まっさらにしたいとき。

1. [flash_nuke.uf2](https://datasheets.raspberrypi.com/soft/flash_nuke.uf2) をダウンロードする
2. BOOT ボタンを押しながらつなぎ、「RPI-RP2」に flash_nuke.uf2 をコピーする（Pico Studio の「.uf2 ファイルを選ぶ」でもよい）
<!-- python -->

3. フラッシュがすべて消える。もう一度 MicroPython を書き込む

<!-- /python -->
<!-- cpp -->

3. フラッシュがすべて消える（9章のフラッシュの記録も消える）。もう一度プログラムを書き込む

<!-- /cpp -->

> ファイルが全部消えるので、残したいものは先にコピーしておいてください（9章の「PC に持ってくる」）。

## 調べるときのコツ

- エラーの最後の行をそのまま検索する
<!-- python -->

- 「MicroPython」「Pico」「センサーの型番」を組み合わせて検索する
- 関数や引数の意味は、コードの単語をクリックすると出る（0章）
- 3章の [RP2 クイックリファレンス](https://docs.micropython.org/en/latest/rp2/quickref.html) と [Random Nerd Tutorials](https://randomnerdtutorials.com/projects-raspberry-pi-pico/) は、たいていの疑問に答えがある

<!-- /python -->
<!-- cpp -->

- 「pico sdk」と関数名やエラーの言葉を組み合わせて検索する
- 関数の使い方は [Pico SDK の API ドキュメント](https://www.raspberrypi.com/documentation/pico-sdk/) で関数名を探す
- 書き方の例は [pico-examples](https://github.com/raspberrypi/pico-examples) で、使いたい機能（i2c、adc、pwm など）のフォルダを見る
- 関数や引数の意味は、コードの単語をクリックすると出る（0章）

<!-- /cpp -->
