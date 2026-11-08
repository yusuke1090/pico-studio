// RGB LED を光らせる
// ピン番号はボードによって違う（例: 23, 16）。光らなければ変えてみる
#include <cstdio>
#include "pico/stdlib.h"
#include "ws2812.h"

Ws2812 rgb(23);

int main() {
    stdio_init_all();
    if (!rgb.begin()) printf("PIO の準備に失敗しました\n");

    const uint8_t colors[][3] = {{30, 0, 0}, {0, 30, 0}, {0, 0, 30}, {30, 30, 30}, {0, 0, 0}};
    while (true) {
        for (auto& c : colors) {
            rgb.put(c[0], c[1], c[2]);
            sleep_ms(500);
        }
    }
}
