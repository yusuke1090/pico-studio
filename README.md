# Pico Studio

Raspberry Pi Pico（RP2040 / RP2350）を、ブラウザから操作するためのローカルツール。MicroPython と C++（Pico SDK）の両方に対応。

- ピコとPCの接続を確認する（USB認識・シリアル接続・MicroPythonの応答）
- ブラウザで Python のコードを書き、ボタン1つでピコの上で実行する
- 実行結果をリアルタイムに表示し、`input()` への入力やREPLのコマンドを送る
- ピコの中のファイルを一覧・開く・保存・削除する（`main.py` に保存すると電源オンで自動実行）
- BOOTSELモードのピコに MicroPython（.uf2）を書き込む
- **C++ モード**: コード欄で「C++」を選ぶと、ボタン1つで PC でビルド → ピコを自動で書き込みモードにする → 書き込む → `printf` の出力を表示する。ビルドエラーの行をクリックすると、その行に飛ぶ
- 教科書のような**ガイド**を横に表示しながら操作できる。コード例は「エディタに入れる」ですぐ実行できる。ガイドも Python / C++ を切り替えて読める

サーバーは自分のPC（`127.0.0.1`）だけで動き、外部には公開しない。

![画面のイメージ](docs/screenshot.png)

## 必要なもの

- Linux（Ubuntu で確認）
- Python 3.10 以上
- pyserial

```sh
sudo apt install python3-serial
```

C++ も使うときは、さらに次のものが必要（くわしくはガイド14章）。

```sh
sh cpp/setup-sdk.sh          # apt でコンパイラなど、~/pico/pico-sdk に Pico SDK、~/apps/pico-cpp にプロジェクト、~/.local/bin に picotool
python3 cpp_build.py check   # そろっているか確かめる
```

Pico SDK は `~/pico/pico-sdk` か、環境変数 `PICO_SDK_PATH` の場所から探す。
コマンドでビルドするプロジェクトだけを作るときは `python3 cpp_build.py init [フォルダ]`（フォルダの `.cpp` が1つずつプログラムになる `CMakeLists.txt` ができる）。

## 起動のしかた

```sh
./start.sh
```

ブラウザで http://localhost:8765 が開く。止めるときはターミナルで `Ctrl + C`。

ポート番号を変えたいとき:

```sh
PORT=9000 ./start.sh
# または
python3 server.py --port 9000
```

## 使い方

くわしくはガイドの [0. Pico Studio の使い方](guide/00-studio.md) にまとめてある。

1. ピコを USB ケーブルでつなぐ（充電専用ケーブルでは認識しない）
2. 画面上部のポート欄で「(ピコ)」と書かれたポートを選び、「接続」を押す
3. 左の「接続の確認」が3つとも緑になればOK
4. 真ん中にコードを書いて「▶ 実行」（`Ctrl + Enter`）
5. 止めるときは「■ 停止」
6. 残しておきたいコードは「ピコに保存」（`Ctrl + S`）。名前を `main.py` にすると、電源を入れたときに自動で動く

「サンプルを選ぶ」から、LED の点滅・温度センサー・PCとの送受信などのサンプルを読み込める。

### C++ で使うとき

1. コード欄の左上で **C++** を選び、ボードの種類（Pico / Pico W / Pico 2 / Pico 2 W）を選ぶ
2. 「接続の確認」の3つ目「C++ の開発環境」が緑になっていることを確かめる
3. 「▶ ビルドして書き込む」（`Ctrl + Enter`）。ピコに MicroPython が入っていても、C++ のプログラムが入っていても、BOOT を押さずに書き込める（初回のビルドは数分）
4. 「PC に保存」（`Ctrl + S`）は `~/apps/pico-cpp`（環境変数 `PICO_CPP_DIR` で変えられる）に保存する。そこに置いた `.h` は `#include` できる

`http://localhost:8765/#lang=cpp` のように開くと、C++ を選んだ状態で始まる。

### MicroPython がまだ入っていないとき

1. ピコの **BOOT** ボタンを押したまま USB をつなぐ
2. 「RPI-RP2」というドライブが出てくると、画面に「最新の MicroPython を書き込む」ボタンが出る
3. ボタンを押すと、[micropython.org](https://micropython.org/download/RPI_PICO/) から最新版をダウンロードして書き込む
   （手元の .uf2 ファイルを選んで書き込むこともできる）
4. 数秒でピコが再起動するので、「更新」を押してから接続する

## ガイド

画面右上の「📘 ガイド」で、ラズパイピコの使い方をまとめたガイドを横に表示できる。
GitHub 上でも [guide/](guide/) フォルダの Markdown をそのまま読める。

4章から先は Python と C++ の両方で書いてあり、画面の言語の選択で切り替わる。

| 章 | 内容 |
| --- | --- |
| [0. Pico Studio の使い方](guide/00-studio.md) | しくみ、起動と終了、接続と権限の設定、画面の見方、実行・停止・保存、ファイルの確認、ガイドの使い方、関数・引数の説明（スクリーンショット付き） |
| [1. ラズパイピコとは](guide/01-pico.md) | マイコンとは、ピコの種類、ボードの各部、BOOT・USR・RST、書き込みモード、MicroPython と C/C++、用語集 |
| [2. コマンドで操作する](guide/02-cli.md) | Pico Studio を使わない操作の順番、mpremote での接続確認・実行・停止・保存・ファイル確認・REPL、ボタンとの対応 |
| [3. マイコンでできること・おすすめリンク](guide/03-usecases.md) | 使い道、牛の行動監視 IoT の流れ、向き・不向き、そろえる部品、リンク集と読む順番 |
| [4. はじめての操作](guide/04-first-steps.md) | MicroPython の書き込み、REPL、はじめてのプログラム、Lチカ（ボード・外付け・RGB）、main.py、ボタン |
| [5. ピンと電源の基本](guide/05-pins.md) | ピン配置図、電源、GPIO とプルアップ、ADC（ボリューム）、PWM、I2C/SPI/UART、注意点 |
| [6. センサーのつなぎ方](guide/06-wiring.md) | ブレッドボード、ジャンパーワイヤー、ピンヘッダの付け方、I2C の配線図と手順、I2C スキャン |
| [7. センサーの操作](guide/07-sensors.md) | レジスタ、バイト列の変換、MPU-6050（加速度）・BMP280（気圧）の読み取り、一定間隔のサンプリング |
| [8. おすすめのセンサー](guide/08-sensor-picks.md) | 最初に使うセンサー、農業向けのセンサー、選ぶときの注意、SHT31 と土壌水分センサーの配線とコード、商品の説明の読み方（ADC コンバータなど） |
| [9. データの記録と送信](guide/09-data.md) | CSV 保存と PC への持ち出し、USB で PC に送って保存、メモリの注意 |
| [10. 機械学習モデルの導入](guide/10-ml.md) | 特徴量、データ収集（手で試す方法）、PC で決定木を学習、成績表の読み方、ピコで推論、大きなモデルの選択肢 |
| [11. 困ったとき](guide/11-trouble.md) | つながらないときの流れ図、接続・エラー・動作のトラブル、コマンドでの確認、初期化 |
| [12. ラズパイとピコの実装の比較](guide/12-compare.md) | Linux との違い、ssh・scp・systemd との対応、同じプログラムの実装手順、複数の処理の動かし方、つまずきやすいところ、使い分け |
| [13. 実際の開発の流れ](guide/13-development.md) | 牛の行動判定システムを例にした開発の順番、首輪・受信機・スマホの役割分担、無線の選び方、電池の計算、試験のしかた |
| [14. C++ の開発環境と基本](guide/14-cpp.md) | Pico SDK の準備、Pico Studio のビルドのしくみ、CMake でのビルドと書き込み、MicroPython との対応表、mpu6050.h、MicroPython に戻す |
| [15. マイコン向けの C++ の書き方](guide/15-cpp-style.md) | 型の選び方、float と整数、メモリの置き場所、使ってよい標準ライブラリ、エラーの扱い、クラスとファイルの分け方、状態機械 |
| [16. 割り込み・タイマー・2つのコア](guide/16-cpp-interrupts.md) | GPIO の割り込み、くり返しタイマー、リングバッファ、2つのコアと FIFO、クリティカルセクション |
| [17. 省電力と長く動かすための工夫](guide/17-cpp-power.md) | 電力を減らす方法、電池の電圧、ウォッチドッグ、設定のフラッシュ保存 |
| [18. 製品にするための準備](guide/18-cpp-product.md) | PC でのテスト、バージョンの埋め込み、Debug Probe と gdb、量産の書き込み、ユニーク ID、出荷前のチェックリスト |

`http://localhost:8765/#chapter=5` のように開くと、その章を直接表示する。

### ガイドの書き方

- 章は `guide/*.md`（Markdown）。順番とタイトルは `guide/chapters.json` で決める
- 言語ごとの説明は `<!-- python -->` 〜 `<!-- /python -->`、`<!-- cpp -->` 〜 `<!-- /cpp -->` で囲む。画面で選んでいる言語の部分だけ表示される（印の行は、それだけで1行にする）
- ` ```python run ` / ` ```cpp run ` で始めたコードには「エディタに入れる」ボタンが付く（ピコで動くコード。C++ は `main` まである1つのプログラムにして、最初に `stdio_init_all()` を呼ぶ）。
  ` ```python ` は PC で動かすコード、` ```cpp ` は C++ のコード、` ```cmake ` は CMakeLists.txt、` ```text ` は説明用
- 画像は `guide/images/` に置いて `![説明](images/ファイル名.png)` と書く（png / jpg / gif / webp / svg）
- 番号付きの手順の途中に画像やコードをはさんでも、続きの番号（例: `4.`）から書けばその番号から表示される
- 手順の下に2文字以上字下げした `- ` を書くと、入れ子の箇条書きになる
- 動画も同じ書き方で表示できる
  - 動画ファイル: `guide/videos/` などに置いて `![説明](videos/ファイル名.mp4)`（mp4 / webm）
  - YouTube: `![説明](https://www.youtube.com/watch?v=動画ID)` と書くと、埋め込みで再生できる
- コードの関数・引数をクリックしたときの説明は `guide/glossary.json` に書く
  - キーは `"関数名.引数名"`（例: `"train_test_split.stratify"`）か `"単語"`（例: `"fit"`、`"Pin.OUT"`）
  - 関数名は最後の部分だけ（`serial.Serial` なら `Serial`）。`"関数名.引数名"` があれば、そちらが優先される
  - コマンドの説明は `"$ コマンド"` の形で書く（例: `"$ sudo"`、`"$ apt install"`、`"$ ls -l"`）。` ```bash ` のコードと、`mpremote ls` のようなインラインのコマンドで出る
  - 説明の先頭の行を `語源: 〜` にすると、吹き出しの中で折りたたんで表示する

## 権限の設定（初回だけ）

Linux では、そのままだとシリアルポートを開く権限がないことがある。
次の udev ルールを入れると、ピコをつないだときにログイン中のユーザーが使えるようになる。

```sh
sudo cp 70-pico-studio.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

入れたあとは、ピコを一度抜いてつなぎ直す。

> 以前の `99-pico-studio.rules` を入れていた場合は、番号が大きすぎて効かない（`uaccess` は 73 番のルールで処理されるため）。
> `sudo rm /etc/udev/rules.d/99-pico-studio.rules` で消してから、上の手順で入れ直す。

udev ルールの代わりに、`dialout` グループに入る方法もある（ログインし直しが必要）。

```sh
sudo usermod -aG dialout $USER
```

## うまくいかないとき

| 症状 | 確認すること |
| --- | --- |
| ポートが見つからない | ケーブルがデータ通信対応か。BOOT ボタンを押しながらつなぐと「RPI-RP2」が出るか |
| 「ポートを開く権限がありません」 | 上の「権限の設定」をする |
| 「MicroPython の応答がありません」 | MicroPython が書き込まれているか。Thonny や mpremote が同じポートを使っていないか |
| 実行が止まらない | 「■ 停止」を押す。それでもだめなら「切断」→ ケーブルを抜き差し |

## 仕組み

```
ブラウザ (static/index.html)
   │  HTTP (localhost:8765)
   ▼
server.py ── pyserial ──▶ /dev/ttyACM0 ──▶ ピコ (MicroPython / C++)
   │
   └─ cpp_build.py ── cmake / make（Pico SDK）──▶ app.uf2 ──▶ RPI-RP2 ドライブ
```

- `server.py` が USB シリアルでピコとつながり、MicroPython の **raw REPL**
  （`Ctrl-A` で入る、プログラムを丸ごと送って実行するモード）でコードを実行する
- 実行中の出力はサーバーが受け取り、ブラウザが 0.15〜0.4 秒ごとに取りに行って表示する
- ファイル操作も、ピコの上で小さな Python コードを実行して行う
- C++ では、`cpp_build.py` がコードを `~/.cache/pico-studio/cpp/app/main.cpp` に書いて CMake でビルドする。
  書き込みモードには、MicroPython なら `machine.bootloader()`、Pico SDK のプログラムなら 1200 bps でポートを開いて閉じる合図で切り替え、
  `RPI-RP2` ドライブに .uf2 をコピーする。再起動したら、シリアルポートを出力の表示だけに使う（REPL は使わない）
- 他のサイトから勝手に操作されないように、サーバーは `127.0.0.1` だけで待ち受け、
  別のオリジンからの POST は拒否する

## ファイル構成

```
server.py               ローカルサーバー（ピコとの通信と API）
cpp_build.py            C++ モード（ビルド・書き込みモードへの切り替え・書き込み・PC のファイル）。init / check のコマンドもある
cpp/setup-sdk.sh        C++ の開発環境をまとめて入れるスクリプト
cpp/include/            C++ で #include できるヘッダー（mpu6050.h、ws2812.h）
cpp/samples/            C++ のサンプル（1行目のコメントがサンプルの名前）
static/index.html       画面（HTML / CSS / JavaScript を1ファイルに）
guide/                  ガイド（Markdown・図）。画面の横に表示される
start.sh                起動してブラウザを開くスクリプト
70-pico-studio.rules    シリアルポートの権限を設定する udev ルール
tests/fake_pico.py      テスト用の「偽のピコ」
tests/test_cpp_mode.py  C++ モードのテスト（偽の cmake / make / SDK を使う）
```

## ピコなしで試す（開発用）

`tests/fake_pico.py` は、MicroPython の REPL のやり取りをまねる偽のピコ。
疑似端末（`/dev/pts/N`）を作るので、実機がなくても画面や API の動作を確かめられる。

```sh
python3 tests/fake_pico.py      # 表示された /dev/pts/N を覚えておく
./start.sh                      # 別のターミナルで
curl -X POST -H 'Content-Type: application/json' \
     -d '{"port":"/dev/pts/N"}' http://localhost:8765/api/connect
```

中身は CPython で実行しているので、`machine` などピコ専用のモジュールは使えない。

C++ モードは、偽の cmake / make / Pico SDK と偽の書き込みドライブでテストできる。

```sh
python3 tests/test_cpp_mode.py
```

## API

| メソッド | パス | 内容 |
| --- | --- | --- |
| GET | `/api/ports` | シリアルポートの一覧と BOOTSEL モードの状態 |
| GET | `/api/state?since=N` | 接続状態と、N 番より後の出力 |
| GET | `/api/info` | MicroPython のバージョン・空き容量 |
| GET | `/api/files` | ピコのファイル一覧 |
| GET | `/api/file?name=...` | ファイルの中身 |
| POST | `/api/connect` `{"port","mode"}` | 接続（`mode` が `"cpp"` なら出力の表示だけ） |
| POST | `/api/disconnect` | 切断 |
| POST | `/api/run` `{"code"}` | コードを実行 |
| POST | `/api/stop` | 実行中のプログラムを止める（Ctrl-C） |
| POST | `/api/send` `{"text"}` | 1行送る（REPL や `input()` 用） |
| POST | `/api/reset` | ソフトリセット（`main.py` が実行される） |
| POST | `/api/file` `{"name","content"}` | ファイルを保存 |
| POST | `/api/delete` `{"name"}` | ファイルを削除 |
| POST | `/api/flash` | 送った .uf2 を書き込む |
| POST | `/api/flash-latest` | 最新の MicroPython をダウンロードして書き込む |
| GET | `/api/cpp/env` | C++ の開発環境（SDK・コンパイラ）の確認 |
| GET | `/api/cpp/samples` | C++ のサンプル |
| GET | `/api/cpp/files` | PC の C++ ファイルの一覧（`~/apps/pico-cpp`） |
| GET | `/api/cpp/file?name=...` | PC の C++ ファイルの中身 |
| POST | `/api/cpp/run` `{"code","board"}` | ビルドして書き込み、出力の表示を始める |
| POST | `/api/cpp/stop` | ビルドを止める |
| POST | `/api/cpp/file` `{"name","content"}` | PC に保存 |
| POST | `/api/cpp/delete` `{"name"}` | PC のファイルを削除 |
