// LED を点滅させる
// 公式ピコは 25 番ピン。ボードによって番号が違うことがある（Pico W は別の方法が必要）
#include <cstdio>
#include "pico/stdlib.h"

constexpr uint LED_PIN = 25;

int main() {
    stdio_init_all();
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    bool on = false;
    while (true) {
        on = !on;
        gpio_put(LED_PIN, on);
        printf("LED %s\n", on ? "ON" : "OFF");
        sleep_ms(500);
    }
}
