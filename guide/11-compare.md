# 11. ラズパイとピコの実装の比較

## この章でわかること

- Linux が動くラズパイと、マイコンのピコの違い
- ssh、scp、systemd などの作業が、ピコでは何にあたるか
- 同じプログラムを、それぞれに実装する手順
- どちらを使えばよいかの判断

ここでの「ラズパイ」は、Raspberry Pi 4 や 5 のような Linux が動くボードのことです。Jetson も同じように考えられます。
コマンドの操作は2章にまとめてあります。

## 一番の違い

**ピコには Linux がありません。** ログインする先も、サービスを管理するしくみもありません。
電源を入れると MicroPython が起動して、自分のプログラムが1つだけ動きます。

| 項目 | ラズパイ | ピコ |
| --- | --- | --- |
| OS | Linux | なし（MicroPython が直接動く） |
| 動くプログラム | 同時にいくつも | 基本的に1つ |
| メモリ | 数GB | 264KB |
| 保存領域 | SD カードなど数十GB | 2MB |
| 消費電力 | 数W | 0.1W 前後 |
| 起動の時間 | 数十秒 | 1秒前後 |
| 電源を急に切る | ファイルが壊れることがある | 基本的に問題ない。書き込み中のデータは失うことがある |
| アナログ入力（ADC） | なし（外付けの部品が必要） | あり |
| ネットワーク | 有線・無線 | なし（Pico W は無線あり） |

数字はおおよその目安です。

## 作業の対応表

| やること | ラズパイ | ピコ |
| --- | --- | --- |
| つなぐ | `ssh pi@raspberrypi.local` | USB でつなぐ |
| 対話で試す | `python3` | `mpremote repl` |
| ファイルを送る | `scp logger.py pi@raspberrypi.local:` | `mpremote cp logger.py :logger.py` |
| 実行する | `python3 logger.py` | `mpremote run logger.py` |
| 止める | Ctrl + C | Ctrl + C のあと `mpremote soft-reset` |
| ファイルを見る | `ls` | `mpremote ls` |
| ライブラリを入れる | `pip install` や `apt install` | `mpremote mip install` |
| 起動時に自動で動かす | systemd のサービス | `main.py` を置く |
| 再起動する | `sudo systemctl restart logger` | `mpremote reset` |
| ログを見る | `journalctl -u logger` | ファイルに書いて `mpremote cat` で読む |
| 落ちたら自動で再起動 | サービスの `Restart=always` | `machine.WDT`（ウォッチドッグ）など |
| OS を更新する | `sudo apt upgrade` | `.uf2` を書き込み直す |
| シェルスクリプト | ラズパイの中に置く | PC に置く |

## 同じプログラムを実装する

センサーを記録する `logger.py` を、電源を入れたら自動で動くようにします。

### ラズパイの場合

PC からファイルを送って、ログインします。

```bash
scp logger.py pi@raspberrypi.local:/home/pi/
ssh pi@raspberrypi.local
```

サービスのファイルを作ります。

```bash
sudo nano /etc/systemd/system/logger.service
```

```text
[Unit]
Description=Sensor logger

[Service]
ExecStart=/usr/bin/python3 /home/pi/logger.py
Restart=always

[Install]
WantedBy=multi-user.target
```

サービスを有効にして、動かし始めます。

```bash
sudo systemctl enable --now logger.service
```

### ピコの場合

ファイルを `main.py` という名前で保存して、再起動するだけです。

```bash
mpremote cp logger.py :main.py
mpremote reset
```

サービスのファイルは要りません。`main.py` という名前が、「起動時に動かす」という設定を兼ねています。

## コードの違い

どちらも Python で書けますが、ピンを動かすライブラリが違います。LED の点滅で比べます。

ラズパイのコードです（GPIO17 に LED をつないだ場合）。

```python
from gpiozero import LED
import time

led = LED(17)
while True:
    led.toggle()
    time.sleep(0.5)
```

ピコのコードです。

```python run
from machine import Pin
import time

led = Pin(25, Pin.OUT)
while True:
    led.toggle()
    time.sleep(0.5)
```

| 機能 | ラズパイ | ピコ |
| --- | --- | --- |
| GPIO | gpiozero | `machine.Pin` |
| I2C | smbus2 | `machine.I2C` |
| アナログ入力 | 外付けの部品とそのライブラリ | `machine.ADC` |
| 使える Python | 通常の Python。numpy なども使える | MicroPython。機能が少ない |

## Linux の感覚でつまずきやすいところ

- **`pip install` は使えません。** ピコのライブラリは `mpremote mip install` で入れます。PC 用のライブラリは、そのままでは動きません
- **`print` の出力は残りません。** USB でつないでいるときに見えるだけです。残したいときはファイルに書きます（8章）
- **`main.py` がエラーで止まると、そのまま止まります。** 自動では再起動しません。長く動かすなら、エラーの処理やウォッチドッグを入れます
- **ファイルの書き込みは控えめにします。** 保存領域が小さく、書き込みの回数にも寿命があります（8章）
- **ポートは1つのソフトでしか使えません。** ssh のように、同時に複数の接続はできません
- **シェルスクリプトはピコで動きません。** 手順をまとめたいときは PC に置きます

## 手順をスクリプトにする

ラズパイへの配置をスクリプトにするのと同じように、ピコへの配置も PC 側のスクリプトにできます。
次の内容を `deploy.sh` という名前で保存します。

```bash
#!/bin/sh
mpremote cp main.py :main.py
mpremote reset
```

コードを直したら、次のコマンドでピコに反映します。

```bash
sh deploy.sh
```

## どちらを使うか

| 目的 | 向いているもの |
| --- | --- |
| 電池で長く動かす | ピコ |
| センサーを決まった間隔で読む | ピコ |
| 電源を急に切られる場所で使う | ピコ |
| カメラの画像を扱う | ラズパイ |
| 大きな機械学習モデルを動かす | ラズパイ、Jetson |
| Web サーバーやデータベースを動かす | ラズパイ |

両方を組み合わせることもできます。ピコが現場でセンサーを読み、ラズパイが受け取って保存や分析をする形です。USB での受け渡しは8章に書いてあります。

## まとめ

- ピコに Linux はない。ssh も systemd もなく、USB と mpremote で操作する
- `scp` は `mpremote cp`、systemd のサービスは `main.py` にあたる
- コードは同じ Python でも、ピンを動かすライブラリが違う
- 手順をまとめるスクリプトは PC に置く
- 省電力とセンサーの読み取りはピコ、重い処理はラズパイが向いている
