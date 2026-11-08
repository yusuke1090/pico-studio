// PC と送受信する
// 下の「送信」欄に数字を入れると、2倍にして返す
#include <cstdio>
#include <cstdlib>
#include "pico/stdlib.h"

int main() {
    stdio_init_all();
    char line[64];
    int len = 0;

    while (true) {
        int c = getchar_timeout_us(100 * 1000);   // 0.1 秒だけ待つ。来なければ PICO_ERROR_TIMEOUT
        if (c == PICO_ERROR_TIMEOUT) continue;
        if (c == '\r' || c == '\n') {
            if (len == 0) continue;
            line[len] = '\0';
            char* end;
            float n = strtof(line, &end);
            if (end != line && *end == '\0') printf("受信: %g → 2倍: %g\n", n, n * 2);
            else printf("受信した文字: %s\n", line);
            len = 0;
        } else if (len < static_cast<int>(sizeof(line)) - 1) {
            line[len++] = static_cast<char>(c);
        }
    }
}
