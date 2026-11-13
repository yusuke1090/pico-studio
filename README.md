# Pico Studio

Raspberry Pi Pico（RP2040 / RP2350）が**つながっているかを確かめる**ためのローカルツールと、C++ と VS Code でピコを開発して**製品にするまで**のガイド。

C++ の開発は VS Code の拡張機能「Raspberry Pi Pico」で行い、Pico Studio は次のことに使う。

- ピコが USB で見えているか、何が動いているか（C++ のプログラム / MicroPython / 書き込みモード）を確かめる
- C++ の開発環境（VS Code の拡張機能・Pico SDK・コンパイラ・picotool）がそろっているかを確かめる
- `printf` の出力を見て、ピコに1行送る
- `.uf2` を書き込む（MicroPython や、VS Code でビルドしたもの）
- MicroPython のコードをすぐ試す（配線やセンサーの下調べ）
- 右上の「📚 ガイド」で、ガイド（[ラズパイピコ開発ガイド](https://yusuke1090.github.io/textbooks/?b=pico)）を教科書のページで開く

サーバーは自分のPC（`127.0.0.1`）だけで動き、外部には公開しない。

![画面のイメージ](https://yusuke1090.github.io/textbooks/books/pico/images/studio-screen.svg)

## 必要なもの

- Linux（Ubuntu で確認）
- Python 3.10 以上と pyserial
- C++ の開発には VS Code と拡張機能「Raspberry Pi Pico」（ガイド2章）

```sh
sudo apt install python3-serial
sudo cp 70-pico-studio.rules /etc/udev/rules.d/    # ピコを sudo なしで使う（シリアルポートと picotool）
sudo udevadm control --reload-rules                 # 入れたら、ピコを一度抜いてつなぎ直す
```

開発環境がそろっているかは、画面の「C++ の開発環境」か、次のコマンドで確かめられる。

```sh
python3 devenv.py check
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

くわしくはガイドの [5. Pico Studio でつながりを確かめる](https://yusuke1090.github.io/textbooks/?b=pico#ch=5) にまとめてある。

1. ピコを USB ケーブルでつなぐ（充電専用ケーブルでは認識しない）
2. ポート欄で「(ピコ・…)」と書かれたポートを選び、「接続」を押す
3. 左の「接続の確認」で、USB・シリアル・動いているプログラム・C++ の開発環境を確かめる
4. C++ のプログラムが動いていれば、`printf` の出力が出力欄に出る。MicroPython なら、コード欄のコードを「▶ 実行」で試せる（付録E）

つなぎ方（MicroPython の REPL か、出力の表示だけか）は、USB の番号（MicroPython は `2e8a:0005`）から自動で決める。

## ガイド

ガイド（ラズパイピコ開発ガイド）は、教科書のリポジトリ [textbooks](https://github.com/yusuke1090/textbooks) の `books/pico/` にあり、[教科書のページ](https://yusuke1090.github.io/textbooks/?b=pico) で読む（スマホでも読める。目次・付箋・線・メモ・言葉の説明もそちら）。
Pico Studio の画面には出さない（右上の「📚 ガイド」は、教科書のページを開くリンク）。

ガイドの ` ```cpp run ` のプログラムが本物の Pico SDK でビルドできるかは、この PC の開発環境を使う `tests/build_guide_cpp.py` で確かめる（下の「テスト」）。ガイドは `~/apps/textbooks/books/pico` から読む（別の場所なら環境変数 `PICO_GUIDE`）。

## うまくいかないとき

| 症状 | 確認すること |
| --- | --- |
| ポートが見つからない | ケーブルがデータ通信対応か。BOOT ボタンを押しながらつなぐと「RPI-RP2」が出るか。USB を使わないプログラムが動いていないか |
| 「ポートを開く権限がありません」 | 上の udev ルールを入れて、ピコを抜き差しする |
| 「MicroPython の応答がありません」 | C++ のプログラムが動いていないか。VS Code の Serial Monitor などが同じポートを使っていないか |
| 「サーバーが古いままです」 | `Ctrl + C` で止めて `./start.sh` で起動し直す |

ガイドの [付録B. 困ったとき](https://yusuke1090.github.io/textbooks/?b=pico#ch=19) にくわしくある。

## 仕組み

```
ブラウザ (static/index.html)
   │  HTTP (localhost:8765)
   ▼
server.py ── pyserial ──▶ /dev/ttyACM0 ──▶ ピコ（C++ のプログラム / MicroPython）
   │
   └─ devenv.py ── ~/.vscode/extensions, ~/.pico-sdk, ~/pico/pico-sdk を見て、開発環境を確かめる
```

- `server.py` が USB シリアルでピコとつながる。MicroPython なら **raw REPL**（`Ctrl-A` で入る、プログラムを丸ごと送って実行するモード）でコードを実行し、C++ のプログラムなら出力を表示するだけにする
- 実行中の出力はサーバーが受け取り、ブラウザが 0.15〜0.4 秒ごとに取りに行って表示する
- 他のサイトから勝手に操作されないように、サーバーは `127.0.0.1` だけで待ち受け、別のオリジンからの POST は拒否する

## ファイル構成

```
server.py               ローカルサーバー（ピコとの通信と API）
devenv.py               C++ の開発環境の確認（check）と、コマンド用のプロジェクトの用意（init）
static/index.html       画面（HTML / CSS / JavaScript を1ファイルに）
cpp/include/            ガイドで使うヘッダー（mpu6050.h、ws2812.h）。プロジェクトにコピーして使う
cpp/setup-sdk.sh        コマンドでビルドするための道具をまとめて入れるスクリプト（付録A）
start.sh                起動してブラウザを開くスクリプト
70-pico-studio.rules    ピコを sudo なしで使えるようにする udev ルール
tests/fake_pico.py      テスト用の「偽のピコ」
tests/test_devenv.py    開発環境の確認とプロジェクトの用意、接続の自動判定のテスト
tests/build_guide_cpp.py  ガイド（~/apps/textbooks/books/pico）の C++ のプログラムを、本物の Pico SDK で全部ビルドして確かめる
```

## テスト・ピコなしで試す（開発用）

```sh
python3 tests/test_devenv.py
python3 tests/build_guide_cpp.py pico pico2   # ガイドの C++（```cpp run）を Pico と Pico 2 でビルド。Pico SDK が必要
```

`build_guide_cpp.py` は、エラーや警告をガイドのファイルと行（例: `textbooks/books/pico/09-sensors.md:325`）で表示する。17章の PC 用テストも g++ で動かす。

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
| GET | `/api/ports` | シリアルポートの一覧（動いているもの `kind` つき）と BOOTSEL モードの状態 |
| GET | `/api/state?since=N` | 接続状態（`mode`: `python` か `cpp`）と、N 番より後の出力 |
| GET | `/api/env` | C++ の開発環境（VS Code の拡張機能・SDK・コンパイラ・picotool） |
| GET | `/api/info` | MicroPython のバージョン・空き容量 |
| GET | `/api/files` | ピコのファイル一覧（MicroPython） |
| GET | `/api/file?name=...` | ファイルの中身（MicroPython） |
| POST | `/api/connect` `{"port"}` | 接続。動いているものから、REPL か出力の表示だけかを自動で決める |
| POST | `/api/disconnect` | 切断 |
| POST | `/api/run` `{"code"}` | MicroPython のコードを実行 |
| POST | `/api/stop` | 実行中のプログラムを止める（Ctrl-C） |
| POST | `/api/send` `{"text"}` | 1行送る（REPL、`input()`、`getchar()` 用） |
| POST | `/api/reset` | ソフトリセット（`main.py` が実行される） |
| POST | `/api/file` `{"name","content"}` | ファイルを保存（MicroPython） |
| POST | `/api/delete` `{"name"}` | ファイルを削除（MicroPython） |
| POST | `/api/flash` | 送った .uf2 を書き込む |
| POST | `/api/flash-latest` | 最新の MicroPython をダウンロードして書き込む |
| POST | `/api/clear` | 出力の記録を消す |
