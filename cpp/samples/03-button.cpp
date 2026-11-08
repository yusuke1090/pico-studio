// ボタン（USR）で LED を点ける
// 多くの互換ボードは USR ボタンが GP24。押すと 0 になる
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint LED_PIN = 25;
constexpr uint BTN_PIN = 24;

int main() {
    stdio_init_all();
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_init(BTN_PIN);
    gpio_set_dir(BTN_PIN, GPIO_IN);
    gpio_pull_up(BTN_PIN);

    bool last = false;
    while (true) {
        bool pressed = !gpio_get(BTN_PIN);
        gpio_put(LED_PIN, pressed);
        if (pressed != last) {
            printf(pressed ? "押されている\n" : "離された\n");
            last = pressed;
        }
        sleep_ms(10);
    }
}
