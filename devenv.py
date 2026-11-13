"""C++ の開発環境の確認と、コマンドでビルドするプロジェクトの用意。

    python3 devenv.py check          開発環境がそろっているか確かめる
    python3 devenv.py init [フォルダ]  コマンドでビルドするプロジェクトを作る（省略すると ~/apps/pico-cpp）

C++ の開発はふだん VS Code の拡張機能「Raspberry Pi Pico」で行う。拡張機能は ~/.pico-sdk に
SDK・コンパイラ・picotool を入れるので、それも探す。Pico Studio の「C++ の開発環境」の確認にも使う。
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def guide_dir():
    """ガイド（ピコの教科書）の場所。教科書のリポジトリ ~/apps/textbooks の books/pico を読む。
    別の場所にあるときは、環境変数 PICO_GUIDE で指定する"""
    env = os.environ.get("PICO_GUIDE")
    return Path(env).expanduser().resolve() if env else HERE.parent / "textbooks" / "books" / "pico"
BUNDLED_INCLUDE = HERE / "cpp" / "include"
PROJECT = Path(os.environ.get("PICO_CPP_DIR", Path.home() / "apps" / "pico-cpp"))
PICO_HOME = Path.home() / ".pico-sdk"          # VS Code の拡張機能が使うフォルダ

# Pico Studio が使うライブラリ。使わないものは、リンクのときに自動で取り除かれる
LIBRARIES = ("pico_stdlib hardware_adc hardware_i2c hardware_spi hardware_pwm hardware_uart "
             "hardware_watchdog hardware_flash hardware_sync hardware_timer hardware_clocks "
             "hardware_dma hardware_irq hardware_pio pico_multicore pico_unique_id")

# ~/apps/pico-cpp（コマンドでビルドするプロジェクト）の CMakeLists.txt
PROJECT_CMAKE = """\
# Pico Studio が作ったプロジェクト（python3 ~/apps/pico-studio/cpp_build.py init）
# このフォルダの *.cpp が、1つずつプログラムになる（blink.cpp → build/blink.uf2）。
# test_ で始まるファイルは PC 用のテスト（18章）なので、ピコ用にはビルドしない。
# .cpp を足したり消したりしたら、もう一度 cmake -S . -B build を打つ。
cmake_minimum_required(VERSION 3.13)
{sdk_fallback}include(pico_sdk_import.cmake)        # pico_sdk_init より前に読む
project(pico_cpp C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

# 使うライブラリ（Pico Studio のビルドと同じ）。使わないものはリンクのときに取り除かれる
set(PICO_LIBS {libs})

file(GLOB APP_SOURCES CONFIGURE_DEPENDS "${{CMAKE_CURRENT_LIST_DIR}}/*.cpp")
foreach(src IN LISTS APP_SOURCES)
    get_filename_component(name "${{src}}" NAME_WE)
    if(name MATCHES "^test_")
        continue()
    endif()
    add_executable(${{name}} "${{src}}")
    target_include_directories(${{name}} PRIVATE "${{CMAKE_CURRENT_LIST_DIR}}")
    target_link_libraries(${{name}} ${{PICO_LIBS}})
    if(PICO_CYW43_SUPPORTED)
        target_link_libraries(${{name}} pico_cyw43_arch_none)
    endif()
    pico_enable_stdio_usb(${{name}} 1)     # printf を USB に出す
    pico_enable_stdio_uart(${{name}} 0)    # UART（GP0, GP1）には出さない
    pico_add_extra_outputs(${{name}})      # .uf2 も作る
endforeach()
"""


# PICO_SDK_PATH が設定されていないターミナルでも、~/pico/pico-sdk にあれば使う
SDK_FALLBACK = """\
if(NOT PICO_SDK_PATH AND NOT DEFINED ENV{{PICO_SDK_PATH}} AND EXISTS "$ENV{{HOME}}/pico/pico-sdk")
    set(PICO_SDK_PATH "$ENV{{HOME}}/pico/pico-sdk")
endif()
"""


def project_cmake(fallback=True):
    return PROJECT_CMAKE.format(libs=LIBRARIES, sdk_fallback=SDK_FALLBACK.format() if fallback else "")



BLINK_CPP = """\
// LED を点滅させる（公式ピコは 25 番ピン）
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
        printf("LED %s\\n", on ? "ON" : "OFF");
        sleep_ms(500);
    }
}
"""


def _newest(paths):
    """名前がバージョンのフォルダの中から、一番新しいものを返す"""
    def key(p):
        return [int(x) for x in re.findall(r"\d+", p.name)] or [0]
    paths = [p for p in paths if p.exists()]
    return sorted(paths, key=key)[-1] if paths else None


def sdk_path():
    p = os.environ.get("PICO_SDK_PATH")
    cands = [Path(p).expanduser()] if p else []
    cands.append(Path.home() / "pico" / "pico-sdk")
    vs = _newest(list((PICO_HOME / "sdk").glob("*")))
    if vs:
        cands.append(vs)
    for c in cands:
        if (c / "pico_sdk_init.cmake").exists():
            return c
    return None


def compiler_path():
    found = shutil.which("arm-none-eabi-gcc")
    if found:
        return found
    tc = _newest([p.parent.parent for p in PICO_HOME.glob("toolchain/*/bin/arm-none-eabi-gcc")])
    return str(tc / "bin" / "arm-none-eabi-gcc") if tc else None


def picotool_path():
    """USB の機能がある picotool（ピコを操作できるもの）を探す"""
    cands = [shutil.which("picotool")] + [str(p) for p in sorted(PICO_HOME.glob("picotool/*/picotool/picotool"))]
    for c in cands:
        if not c:
            continue
        try:
            out = subprocess.run([c, "version"], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        if "without USB" not in out:
            return c
    return None


def vscode_extension():
    """VS Code の拡張機能「Raspberry Pi Pico」のバージョン（なければ None）"""
    ext = _newest(list((Path.home() / ".vscode" / "extensions").glob("raspberry-pi.raspberry-pi-pico-*")))
    return ext.name.rsplit("-", 1)[-1] if ext else None


def check():
    sdk = sdk_path()
    version = ""
    if sdk:
        try:
            m = re.findall(r"set\(PICO_SDK_VERSION_(?:MAJOR|MINOR|REVISION) (\d+)\)",
                           (sdk / "pico_sdk_version.cmake").read_text())
            version = ".".join(m)
        except OSError:
            pass
    items = {"vscode": vscode_extension(), "sdk": str(sdk) if sdk else None,
             "compiler": compiler_path(), "picotool": picotool_path()}
    problems = []
    if not items["vscode"]:
        problems.append("VS Code の拡張機能「Raspberry Pi Pico」がありません")
    if not items["sdk"]:
        problems.append("Pico SDK がありません（VS Code で最初のプロジェクトを作ると入ります）")
    if not items["compiler"]:
        problems.append("ARM 用のコンパイラがありません（VS Code で最初のプロジェクトを作ると入ります）")
    return {"ok": bool(items["vscode"] and items["sdk"] and items["compiler"]), "items": items,
            "problems": problems, "sdk_version": version, "home": str(Path.home())}


def init_project(folder=None, quiet=False):
    """コマンドでビルドできるプロジェクトのフォルダを作る。すでにあるファイルは上書きしない。"""
    folder = Path(folder or PROJECT).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    made = []

    def put(name, text):
        p = folder / name
        if not p.exists():
            p.write_text(text, encoding="utf-8")
            made.append(name)

    cm = folder / "CMakeLists.txt"
    if cm.exists() and cm.read_text(encoding="utf-8") == project_cmake(fallback=False):
        cm.write_text(project_cmake(), encoding="utf-8")   # 手を加えていない古い雛形は、新しいものにする
        made.append("CMakeLists.txt（新しい形にしました）")
    put("CMakeLists.txt", project_cmake())
    put(".gitignore", "build/\nbuild-*/\n")
    for h in sorted(BUNDLED_INCLUDE.glob("*.h")):
        put(h.name, h.read_text(encoding="utf-8"))
    if not any(folder.glob("*.cpp")):
        put("blink.cpp", BLINK_CPP)
    sdk = sdk_path()
    if sdk:
        put("pico_sdk_import.cmake", (sdk / "external" / "pico_sdk_import.cmake").read_text())
    if not quiet:
        print(f"{folder} を用意しました")
        for m in made:
            print("  作成:", m)
        if not made:
            print("  （足りないファイルはありませんでした）")
        if not (folder / "pico_sdk_import.cmake").exists():
            print("※ Pico SDK が見つからないので、pico_sdk_import.cmake は作っていません。\n"
                  "  SDK を入れてから（sh ~/apps/pico-studio/cpp/setup-sdk.sh）、もう一度このコマンドを打ってください。")
    return made


def delete_file(name):
    _project_file(name).unlink()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        init_project(sys.argv[2] if len(sys.argv) > 2 else None)
    elif len(sys.argv) >= 2 and sys.argv[1] == "check":
        env = check()
        it = env["items"]
        mark = lambda v: "✓" if v else "✗"
        print(f"{mark(it['vscode'])} VS Code の拡張機能 Raspberry Pi Pico {it['vscode'] or ''}")
        print(f"{mark(it['sdk'])} Pico SDK {env['sdk_version']} {it['sdk'] or ''}")
        print(f"{mark(it['compiler'])} コンパイラ {it['compiler'] or ''}")
        print(f"{mark(it['picotool'])} picotool {it['picotool'] or '（なくても VS Code では書き込める）'}")
        print("OK: C++ を開発できます" if env["ok"] else "足りないもの:\n・" + "\n・".join(env["problems"]))
        sys.exit(0 if env["ok"] else 1)
    else:
        print(__doc__)
