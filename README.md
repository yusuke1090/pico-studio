# Pico Studio

Raspberry Pi Pico（RP2040 / MicroPython）を、ブラウザから操作するためのローカルツール。

- ピコとPCの接続を確認する（USB認識・シリアル接続・MicroPythonの応答）
- ブラウザで Python のコードを書き、ボタン1つでピコの上で実行する
- 実行結果をリアルタイムに表示し、`input()` への入力やREPLのコマンドを送る
- ピコの中のファイルを一覧・開く・保存・削除する（`main.py` に保存すると電源オンで自動実行）
- BOOTSELモードのピコに MicroPython（.uf2）を書き込む
- 教科書のような**ガイド**を横に表示しながら操作できる。コード例は「エディタに入れる」ですぐ実行できる

サーバーは自分のPC（`127.0.0.1`）だけで動き、外部には公開しない。

![画面のイメージ](docs/screenshot.png)

## 必要なもの

- Linux（Ubuntu で確認）
- Python 3.10 以上
- pyserial

```sh
sudo apt install python3-serial
```

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

### MicroPython がまだ入っていないとき

1. ピコの **BOOT** ボタンを押したまま USB をつなぐ
2. 「RPI-RP2」というドライブが出てくると、画面に「最新の MicroPython を書き込む」ボタンが出る
3. ボタンを押すと、[micropython.org](https://micropython.org/download/RPI_PICO/) から最新版をダウンロードして書き込む
   （手元の .uf2 ファイルを選んで書き込むこともできる）
4. 数秒でピコが再起動するので、「更新」を押してから接続する

## ガイド

画面右上の「📘 ガイド」で、ラズパイピコの使い方をまとめたガイドを横に表示できる。
GitHub 上でも [guide/](guide/) フォルダの Markdown をそのまま読める。

| 章 | 内容 |
| --- | --- |
| [0. Pico Studio の使い方](guide/00-studio.md) | 起動、接続と権限の設定、画面の見方、よく使う操作、関数・引数の説明の出し方 |
| [1. ラズパイピコとは](guide/01-pico.md) | マイコンとは、RP2040 の性能、MicroPython と C/C++ |
| [2. マイコンでできること・おすすめリンク](guide/02-usecases.md) | 使い道、向き・不向き、公式ドキュメントや作例のリンク集 |
| [3. はじめての操作](guide/03-first-steps.md) | MicroPython の書き込み、REPL、Lチカ、ボタン |
| [4. ピンと電源の基本](guide/04-pins.md) | ピン配置、電源、GPIO、ADC、I2C/SPI/UART、注意点 |
| [5. センサーのつなぎ方](guide/05-wiring.md) | ブレッドボード、ピンヘッダの付け方、I2C の配線図、I2C スキャン |
| [6. センサーの操作](guide/06-sensors.md) | MPU-6050（加速度）・BMP280（気圧）の読み取り、一定間隔のサンプリング |
| [7. データの記録と送信](guide/07-data.md) | CSV 保存、PC への送信と保存、メモリの注意 |
| [8. 機械学習モデルの導入](guide/08-ml.md) | 特徴量、データ収集、PC で決定木を学習、ピコで推論、大きなモデルの選択肢 |
| [9. 困ったとき](guide/09-trouble.md) | 接続・エラー・動作のトラブルと対処 |

`http://localhost:8765/#chapter=5` のように開くと、その章を直接表示する。

### ガイドの書き方

- 章は `guide/*.md`（Markdown）。順番とタイトルは `guide/chapters.json` で決める
- ` ```python run ` で始めたコードには「エディタに入れる」ボタンが付く（ピコで動くコード）。
  ` ```python ` は PC で動かすコード、` ```text ` は説明用
- 画像は `guide/images/` に置いて `![説明](images/ファイル名.png)` と書く（png / jpg / gif / webp / svg）
- 動画も同じ書き方で表示できる
  - 動画ファイル: `guide/videos/` などに置いて `![説明](videos/ファイル名.mp4)`（mp4 / webm）
  - YouTube: `![説明](https://www.youtube.com/watch?v=動画ID)` と書くと、埋め込みで再生できる
- コードの関数・引数をクリックしたときの説明は `guide/glossary.json` に書く
  - キーは `"関数名.引数名"`（例: `"train_test_split.stratify"`）か `"単語"`（例: `"fit"`、`"Pin.OUT"`）
  - 関数名は最後の部分だけ（`serial.Serial` なら `Serial`）。`"関数名.引数名"` があれば、そちらが優先される

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
server.py ── pyserial ──▶ /dev/ttyACM0 ──▶ ピコ (MicroPython)
```

- `server.py` が USB シリアルでピコとつながり、MicroPython の **raw REPL**
  （`Ctrl-A` で入る、プログラムを丸ごと送って実行するモード）でコードを実行する
- 実行中の出力はサーバーが受け取り、ブラウザが 0.15〜0.4 秒ごとに取りに行って表示する
- ファイル操作も、ピコの上で小さな Python コードを実行して行う
- 他のサイトから勝手に操作されないように、サーバーは `127.0.0.1` だけで待ち受け、
  別のオリジンからの POST は拒否する

## ファイル構成

```
server.py               ローカルサーバー（ピコとの通信と API）
static/index.html       画面（HTML / CSS / JavaScript を1ファイルに）
guide/                  ガイド（Markdown・図）。画面の横に表示される
start.sh                起動してブラウザを開くスクリプト
70-pico-studio.rules    シリアルポートの権限を設定する udev ルール
tests/fake_pico.py      テスト用の「偽のピコ」
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

## API

| メソッド | パス | 内容 |
| --- | --- | --- |
| GET | `/api/ports` | シリアルポートの一覧と BOOTSEL モードの状態 |
| GET | `/api/state?since=N` | 接続状態と、N 番より後の出力 |
| GET | `/api/info` | MicroPython のバージョン・空き容量 |
| GET | `/api/files` | ピコのファイル一覧 |
| GET | `/api/file?name=...` | ファイルの中身 |
| POST | `/api/connect` `{"port"}` | 接続 |
| POST | `/api/disconnect` | 切断 |
| POST | `/api/run` `{"code"}` | コードを実行 |
| POST | `/api/stop` | 実行中のプログラムを止める（Ctrl-C） |
| POST | `/api/send` `{"text"}` | 1行送る（REPL や `input()` 用） |
| POST | `/api/reset` | ソフトリセット（`main.py` が実行される） |
| POST | `/api/file` `{"name","content"}` | ファイルを保存 |
| POST | `/api/delete` `{"name"}` | ファイルを削除 |
| POST | `/api/flash` | 送った .uf2 を書き込む |
| POST | `/api/flash-latest` | 最新の MicroPython をダウンロードして書き込む |
