#pragma once
// RGB LED（WS2812 / NeoPixel）を光らせるクラス。
// ピコの PIO（自由に作れる入出力回路）で、WS2812 の決まった速さの信号を作る。
// PIO のプログラムは pico-examples の ws2812.pio を、組み立て済みの数値にしたもの。
#include <cstdint>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"

class Ws2812 {
public:
    // pin: RGB LED のデータのピン（ボードによって違う。例: 23, 16）
    explicit Ws2812(uint pin, PIO pio = pio0) : pin_(pin), pio_(pio) {}

    bool begin() {
        static const uint16_t instructions[] = {
            0x6221,  // out x, 1   side 0 [2]
            0x1123,  // jmp !x, 3  side 1 [1]
            0x1400,  // jmp 0      side 1 [4]
            0xa442,  // nop        side 0 [4]
        };
        pio_program_t program{};
        program.instructions = instructions;
        program.length = 4;
        program.origin = -1;
        if (!pio_can_add_program(pio_, &program)) return false;
        uint offset = pio_add_program(pio_, &program);
        int sm = pio_claim_unused_sm(pio_, false);
        if (sm < 0) return false;
        sm_ = static_cast<uint>(sm);

        pio_gpio_init(pio_, pin_);
        pio_sm_set_consecutive_pindirs(pio_, sm_, pin_, 1, true);   // ピンを出力にする
        pio_sm_config c = pio_get_default_sm_config();
        sm_config_set_wrap(&c, offset, offset + 3);
        sm_config_set_sideset(&c, 1, false, false);
        sm_config_set_sideset_pins(&c, pin_);
        sm_config_set_out_shift(&c, false, true, 24);       // 24 ビット（緑・赤・青）ずつ送る
        sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_TX);
        constexpr int cycles_per_bit = 10;                   // 3 + 3 + 4
        sm_config_set_clkdiv(&c, clock_get_hz(clk_sys) / (800000.0f * cycles_per_bit));   // 800kHz
        pio_sm_init(pio_, sm_, offset, &c);
        pio_sm_set_enabled(pio_, sm_, true);
        return true;
    }

    // 赤・緑・青を 0〜255 で指定する。LED がいくつもつながっているときは、つないだ順に呼ぶ
    void put(uint8_t r, uint8_t g, uint8_t b) {
        uint32_t grb = (static_cast<uint32_t>(g) << 16) | (static_cast<uint32_t>(r) << 8) | b;
        pio_sm_put_blocking(pio_, sm_, grb << 8u);
    }

private:
    uint pin_;
    PIO pio_;
    uint sm_ = 0;
};
