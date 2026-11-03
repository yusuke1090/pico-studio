# 2. マイコンでできること・おすすめリンク

## この章でわかること

- マイコンがどんなところで使われているか
- 自分のプロジェクトにマイコンが向いているかの判断のしかた
- 勉強に役立つサイト

## マイコンの主な使い道

| 分野 | 例 |
| --- | --- |
| センサーで測る | 温度・湿度・気圧・加速度・照度・土の水分を測って記録する |
| 動かす | モーター、サーボ、LED、ブザー、リレー（家電のオン/オフ）を制御する |
| つなぐ | センサーの値を WiFi や Bluetooth、LoRa で送る（IoT） |
| 入力機器 | 自作キーボード、ゲームコントローラー、MIDI 機器 |
| 見守り | 動物や人の動き、設備の振動を監視して異常を知らせる |
| エッジAI | 小さな機械学習モデルで、その場で音や動きを判定する |

### 例: 牛の行動監視 IoT

首輪にピコと加速度センサーを付けて、牛の動きを測るとします。

1. **センサーで測る**: 加速度センサーで首の動き、気圧センサーで頭の高さの変化を測る（5・6章）
2. **記録する**: 一定時間ごとにデータをまとめて保存する（7章）
3. **判定する**: 「歩行」「採食」「反芻」「起立」などを機械学習で判定する（8章）
4. **送る**: WiFi 付きのボード（Pico W など）で、判定結果をクラウドに送る

マイコンの上で判定まで済ませると、送るデータが「生の加速度」から「行動の種類」になり、通信量と電池を大きく節約できます。

## マイコンが向いている・向いていない

**向いている**
- 電池で長く動かしたい
- 電源を入れたらすぐ動いてほしい
- センサーを決まった間隔で正確に読みたい
- 小さく・安く作りたい

**向いていない（Raspberry Pi 4/5 や PC が向いている）**
- カメラ映像の処理や、大きな AI モデル
- 画面に複雑な表示をしたい
- 大量のデータを保存・集計したい

よくある構成は「**現場ではマイコンが測って送る → クラウドや PC で集めて分析する**」です。

## おすすめリンク

### 公式ドキュメント（まず見るところ）

- [MicroPython RP2 クイックリファレンス](https://docs.micropython.org/en/latest/rp2/quickref.html)
  — ピン・I2C・タイマーなどの書き方が1ページにまとまっている。一番よく使う
- [MicroPython の I2C の説明](https://docs.micropython.org/en/latest/library/machine.I2C.html)
  — センサーとの通信で使う
- [Raspberry Pi Pico Python SDK（PDF）](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf)
  — 公式の MicroPython 入門書。例がたくさんある
- [Raspberry Pi Pico データシート（PDF）](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf)
  — ピン配置図や電源の仕様
- [RP2040 データシート（PDF）](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
  — チップの詳しい仕様。細かいことを調べるとき用
- [MicroPython のダウンロード](https://micropython.org/download/RPI_PICO/)
  — ファームウェア（.uf2）

### チュートリアル・作例

- [Getting started with Raspberry Pi Pico（公式プロジェクト）](https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico)
  — LED・ボタン・センサーを順番に試せる公式チュートリアル
- [Random Nerd Tutorials: Raspberry Pi Pico](https://randomnerdtutorials.com/projects-raspberry-pi-pico/)
  — センサーごとの配線とコードの作例がとても多い
- [Wokwi](https://wokwi.com/)
  — ブラウザ上でピコとセンサーをシミュレーションできる。部品がなくても試せる

### ライブラリ

- [micropython-lib](https://github.com/micropython/micropython-lib)
  — 公式のライブラリ集
- [umqtt.simple](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple)
  — IoT でよく使う MQTT でデータを送るためのライブラリ
- [ulab](https://github.com/v923z/micropython-ulab)
  — MicroPython 用の numpy のようなもの（ファームウェアに組み込んで使う）

### C/C++ で書くとき

- [Pico SDK](https://github.com/raspberrypi/pico-sdk) — 公式の C/C++ 開発キット
- [pico-examples](https://github.com/raspberrypi/pico-examples) — Pico SDK の公式サンプル集
- [arduino-pico](https://github.com/earlephilhower/arduino-pico) — Arduino の書き方でピコを使えるようにするもの

### 機械学習（8章で使う）

- [emlearn](https://github.com/emlearn/emlearn) / [emlearn-micropython](https://github.com/emlearn/emlearn-micropython)
  — scikit-learn のモデルをマイコン用に変換する
- [LiteRT for Microcontrollers（旧 TensorFlow Lite Micro）](https://ai.google.dev/edge/litert/microcontrollers/overview)
  — ニューラルネットをマイコンで動かす
- [pico-tflmicro](https://github.com/raspberrypi/pico-tflmicro) — 上をピコ用に移植したもの（C++）
- [Edge Impulse](https://edgeimpulse.com/) / [ドキュメント](https://docs.edgeimpulse.com/)
  — データ集めから学習・マイコンへの書き出しまでをブラウザでできるサービス
- [scikit-learn の決定木](https://scikit-learn.org/stable/modules/tree.html)

### センサー

- [MPU-6050（加速度・ジャイロセンサー）](https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/)
  — 製品ページ。レジスタの資料もここから
