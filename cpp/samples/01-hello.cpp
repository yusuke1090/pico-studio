// hello: 文字と計算
#include <cstdio>
#include "pico/stdlib.h"

int main() {
    stdio_init_all();
    sleep_ms(1500);                    // PC が出力を受け取れるようになるまで待つ

    printf("hello, pico!\n");
    for (int i = 1; i <= 5; i++) {
        printf("%d x 2 = %d\n", i, i * 2);
    }

    while (true) {                     // main() は終わらないようにする
        sleep_ms(1000);
    }
}
