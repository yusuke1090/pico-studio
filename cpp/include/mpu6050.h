#pragma once
#include <cstdint>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

class Mpu6050 {
public:
    explicit Mpu6050(i2c_inst_t* i2c, uint8_t addr = 0x68) : i2c_(i2c), addr_(addr) {}

    // ピンを設定して、センサーを起こす。成功すれば true
    bool begin(uint sda, uint scl, uint baud = 400 * 1000) {
        i2c_init(i2c_, baud);
        gpio_set_function(sda, GPIO_FUNC_I2C);
        gpio_set_function(scl, GPIO_FUNC_I2C);
        gpio_pull_up(sda);
        gpio_pull_up(scl);

        bool ok = write_reg(0x6B, 0x00)      // スリープ解除
               && write_reg(0x1C, 0x00)      // 加速度 ±2g     → 16384 = 1g
               && write_reg(0x1B, 0x00);     // ジャイロ ±250°/s → 131 = 1°/s
        sleep_ms(100);
        return ok;
    }

    uint8_t who_am_i() {
        uint8_t v = 0;
        read_regs(0x75, &v, 1);
        return v;
    }

    // 加速度 [g] だけを読む（6バイト）
    bool read_accel(float& ax, float& ay, float& az) {
        uint8_t d[6];
        if (!read_regs(0x3B, d, 6)) return false;
        ax = to_i16(d[0], d[1]) / 16384.0f;
        ay = to_i16(d[2], d[3]) / 16384.0f;
        az = to_i16(d[4], d[5]) / 16384.0f;
        return true;
    }

    // 加速度 [g]・角速度 [°/s]・温度 [℃] をまとめて読む（14バイト）
    bool read_all(float acc[3], float gyro[3], float& temp) {
        uint8_t d[14];
        if (!read_regs(0x3B, d, 14)) return false;
        for (int i = 0; i < 3; i++) {
            acc[i] = to_i16(d[i * 2], d[i * 2 + 1]) / 16384.0f;
            gyro[i] = to_i16(d[8 + i * 2], d[9 + i * 2]) / 131.0f;
        }
        temp = to_i16(d[6], d[7]) / 340.0f + 36.53f;
        return true;
    }

private:
    // ビッグエンディアンの2バイトを、符号付き16ビットの数にする（struct.unpack(">h") と同じ）
    static int16_t to_i16(uint8_t hi, uint8_t lo) {
        return static_cast<int16_t>((hi << 8) | lo);
    }

    // writeto_mem と同じ。レジスタの番号と値を続けて送る
    bool write_reg(uint8_t reg, uint8_t value) {
        uint8_t buf[2] = {reg, value};
        return i2c_write_blocking(i2c_, addr_, buf, 2, false) == 2;
    }

    // readfrom_mem と同じ。番号を送ってから、続けて len バイト読む
    bool read_regs(uint8_t reg, uint8_t* dst, size_t len) {
        if (i2c_write_blocking(i2c_, addr_, &reg, 1, true) != 1) return false;   // true = 通信を切らずに続ける
        return i2c_read_blocking(i2c_, addr_, dst, len, false) == static_cast<int>(len);
    }

    i2c_inst_t* i2c_;
    uint8_t addr_;
};
