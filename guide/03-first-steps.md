# 3. はじめての操作

## この章でわかること

- MicroPython をピコに書き込む方法
- Pico Studio でコードを実行する方法
- LED を点滅させる（「Lチカ」）

## MicroPython を書き込む

買ったばかりのピコには、MicroPython が入っていないことがあります。

1. ピコの **BOOT** ボタンを押したまま、USB ケーブルで PC につなぐ
2. つないだらボタンを離す
3. Pico Studio の「接続の確認」に **BOOTSEL モード** と出て、「最新の MicroPython を書き込む」ボタンが表示される
4. ボタンを押すと、自動でダウンロードして書き込む
5. 数秒でピコが再起動するので、「更新」→ ポートを選んで「接続」

> **RST ボタンがあるボード**なら、USB を抜かずに書き込みモードにできます。
> BOOT を押したまま RST を押して離し、そのあと BOOT を離します（1章の「3つのボタン」）。

> 何も出てこないときは、USB ケーブルが充電専用かもしれません。データ通信対応のケーブルに替えてみてください。

## Pico Studio の画面

画面の見方や操作は、0章「Pico Studio の使い方」にまとめてあります。
このガイドのコード例にある **「エディタに入れる」** ボタンを押すと、コード欄にそのまま入ります。

## REPL で1行ずつ試す

出力欄の下の入力欄に、Python を1行ずつ打って「送信」すると、その場で実行されます（REPL）。

```text
>>> 1 + 2
3
>>> import sys
>>> sys.implementation
(name='micropython', version=(1, 26, 1, ''), ...)
```

ちょっとした確認には REPL、まとまったプログラムはコード欄、と使い分けます。

## はじめてのプログラム

```python run
print("hello, pico!")

total = 0
for i in range(1, 11):
    total += i
print("1から10の合計:", total)
```

「エディタに入れる」→「▶ 実行」で、出力欄に結果が出れば成功です。

## LED を点滅させる（Lチカ）

マイコンの最初の一歩は、LED を点滅させること（Lチカ）です。
公式ピコでは、ボード上の LED は **GP25** につながっています。

```python run
from machine import Pin
import time

led = Pin(25, Pin.OUT)   # GP25 を出力にする

for i in range(10):
    led.on()
    time.sleep(0.3)
    led.off()
    time.sleep(0.3)

print("おわり")
```

- `Pin(25, Pin.OUT)`: 25番ピンを「出力」として使う
- `led.on()` / `led.off()`: 3.3V を出す / 0V にする
- `time.sleep(0.3)`: 0.3秒待つ

> Pico W / Pico 2 W では、LED は `Pin("LED", Pin.OUT)` と書きます。
> 互換ボードでは LED のピン番号が違うことがあります。光らなければ、ボードの説明書を確認してください。

## 止めるとき・自動で動かすとき

- 無限ループのプログラムは「■ 停止」で止める（Ctrl-C を送っている）
- コードを **main.py** という名前で「ピコに保存」すると、PC につながなくても、電源を入れたときに自動で動く
- main.py を止めたいときは、Pico Studio で接続すると自動で止まる。消したいときはファイル一覧の「削除」

## ボタンを読む

互換ボードの中には、ユーザーボタン（**USR**、多くは **GP24**）が付いているものがあります。下のコードを実行して USR を押すと「押されている」と出ます。
外付けのボタンなら、ボタンの片側を GPIO、もう片側を GND につなぎます。

```python run
from machine import Pin
import time

button = Pin(24, Pin.IN, Pin.PULL_UP)   # 押していないとき 1、押すと 0

for i in range(50):
    print("押されている" if button.value() == 0 else "-")
    time.sleep(0.2)
```

`Pin.PULL_UP` はピコの中の抵抗で、何もつながっていないときの値を 1 に固定するための設定です（4章で説明）。

## まとめ

- BOOT ボタンを押しながらつなぐと、MicroPython を書き込める
- 「エディタに入れる」→「▶ 実行」でガイドのコードを試せる
- `Pin` で LED やボタンを扱える。main.py に保存すると電源オンで自動実行
