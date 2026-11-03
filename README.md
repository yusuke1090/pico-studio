# Pico Studio

Raspberry Pi Pico（RP2040 / MicroPython）を、ブラウザから操作するためのローカルツール。

- ピコとPCの接続を確認する（USB認識・シリアル接続・MicroPythonの応答）
- ブラウザで Python のコードを書き、ボタン1つでピコの上で実行する
- 実行結果をリアルタイムに表示し、`input()` への入力やREPLのコマンドを送る
- ピコの中のファイルを一覧・開く・保存・削除する（`main.py` に保存すると電源オンで自動実行）
- BOOTSELモードのピコに MicroPython（.uf2）を書き込む

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

## 権限の設定（初回だけ）

Linux では、そのままだとシリアルポートを開く権限がないことがある。
次の udev ルールを入れると、ピコをつないだときにログイン中のユーザーが使えるようになる。

```sh
sudo cp 99-pico-studio.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

入れたあとは、ピコを一度抜いてつなぎ直す。

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
start.sh                起動してブラウザを開くスクリプト
99-pico-studio.rules    シリアルポートの権限を設定する udev ルール
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
