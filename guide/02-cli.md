# 2. コマンドで操作する

## この章でわかること

- Pico Studio を使わず、ターミナルのコマンドだけでピコを操作する方法
- 接続の確認から実行・保存まで、どの順番で何を打てばよいか
- Pico Studio のボタンと、コマンドの対応

コマンドの操作には **mpremote** を使います。MicroPython の公式ツールです。

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
| 何も出ない | 認識されていない | ケーブルと USB ポートを確かめる（10章） |

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

- 行の最初に **`+`** が付いていれば、権限の設定もできています
- `+` がないときは、0章の「ポートを開く権限がありません」の設定をします
- ファイルが見つからないときは、手順2に戻ります

ポートの名前は、次のコマンドでも調べられます。

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

```bash
mpremote run hello.py
```

PC にあるファイルをピコへ送って実行します。結果はターミナルに出ます。ピコにファイルは残りません。

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
