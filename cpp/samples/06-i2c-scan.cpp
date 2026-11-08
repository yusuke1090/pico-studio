// I2C スキャン（SDA=GP4, SCL=GP5）
// つないだセンサーのアドレスを表示する
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

int main() {
    stdio_init_all();
    i2c_init(i2c0, 100 * 1000);
    gpio_set_function(4, GPIO_FUNC_I2C);
    gpio_set_function(5, GPIO_FUNC_I2C);
    gpio_pull_up(4);
    gpio_pull_up(5);

    while (true) {
        printf("スキャン中...\n");
        int found = 0;
        for (int addr = 0x08; addr < 0x78; addr++) {
            uint8_t dummy;
            if (i2c_read_blocking(i2c0, addr, &dummy, 1, false) >= 0) {   // 応答があればそのアドレスにいる
                printf("  見つかった: 0x%02x\n", addr);
                found++;
            }
        }
        printf("%d 個見つかりました\n\n", found);
        sleep_ms(3000);
    }
}
