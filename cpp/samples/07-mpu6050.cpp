// MPU-6050（加速度・角速度）を読む（SDA=GP4, SCL=GP5）
// mpu6050.h は Pico Studio に入っている（ガイド7章）
#include <cstdio>
#include "pico/stdlib.h"
#include "mpu6050.h"

Mpu6050 mpu(i2c0);

int main() {
    stdio_init_all();
    if (!mpu.begin(4, 5)) printf("MPU-6050 が見つかりません。配線を確かめてください\n");

    while (true) {
        float acc[3], gyro[3], temp;
        if (mpu.read_all(acc, gyro, temp)) {
            printf("加速度[g] x=%+.2f y=%+.2f z=%+.2f  角速度[deg/s] x=%+6.1f y=%+6.1f z=%+6.1f\n",
                   acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2]);
        } else {
            printf("読み取りに失敗しました\n");
        }
        sleep_ms(200);
    }
}
