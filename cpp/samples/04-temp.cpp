// 内蔵の温度センサー
#include <cstdio>
#include "pico/stdlib.h"
#include "hardware/adc.h"

int main() {
    stdio_init_all();
    adc_init();
    adc_set_temp_sensor_enabled(true);
    adc_select_input(4);               // 4番 = 内蔵温度センサー

    while (true) {
        float volt = adc_read() * 3.3f / 4096;
        float temp = 27.0f - (volt - 0.706f) / 0.001721f;
        printf("温度: %.1f C\n", temp);
        sleep_ms(1000);
    }
}
