"""Pico Studio の C++ モード: Pico SDK でビルドして、ピコに書き込む。

流れ
1. エディタのコードを作業フォルダ（~/.cache/pico-studio/cpp/app/main.cpp）に書く
2. cmake（初回だけ）と make でビルドして app.uf2 を作る
3. ピコを書き込みモード（BOOTSEL）にする
   - MicroPython が動いていれば machine.bootloader()
   - C++（USB の printf あり）が動いていれば、1200 bps でポートを開く（SDK の決まり）
4. RPI-RP2 ドライブに app.uf2 をコピーする
5. ピコが再起動したら、シリアルモニターとしてつなぎ、printf の出力を表示する
"""

import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

import serial

HERE = Path(__file__).resolve().parent
BUNDLED_INCLUDE = HERE / "cpp" / "include"
SAMPLES = HERE / "cpp" / "samples"
WORK = Path(os.environ.get("PICO_STUDIO_WORK", Path.home() / ".cache" / "pico-studio" / "cpp"))
PROJECT = Path(os.environ.get("PICO_CPP_DIR", Path.home() / "apps" / "pico-cpp"))
BOARDS = ("pico", "pico_w", "pico2", "pico2_w")
SOURCE_EXT = (".cpp", ".h", ".hpp", ".c")
NAME_RE = re.compile(r"^[\w.-]+$")

# Pico Studio が使うライブラリ。使わないものは、リンクのときに自動で取り除かれる
LIBRARIES = ("pico_stdlib hardware_adc hardware_i2c hardware_spi hardware_pwm hardware_uart "
             "hardware_watchdog hardware_flash hardware_sync hardware_timer hardware_clocks "
             "hardware_dma hardware_irq hardware_pio pico_multicore pico_unique_id")

CMAKE_TEMPLATE = """\
# Pico Studio が自動で作るファイル（書き換えても、次のビルドで元に戻る）
cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(studio_app C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(app app/main.cpp)
target_include_directories(app PRIVATE "{project}" ${{CMAKE_CURRENT_LIST_DIR}}/include)
target_link_libraries(app {libs})
if (PICO_CYW43_SUPPORTED)
    target_link_libraries(app pico_cyw43_arch_none)
endif()
pico_enable_stdio_usb(app 1)
pico_enable_stdio_uart(app 0)
pico_add_extra_outputs(app)
"""


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


class BuildError(Exception):
    pass


# ---------- 開発環境 ----------
def sdk_path():
    p = os.environ.get("PICO_SDK_PATH")
    cands = [Path(p).expanduser()] if p else []
    cands.append(Path.home() / "pico" / "pico-sdk")
    for c in cands:
        if (c / "pico_sdk_init.cmake").exists():
            return c
    return None


def check_env():
    """C++ でビルドするのに必要なものがそろっているかを返す。"""
    sdk = sdk_path()
    tools = {t: shutil.which(t) for t in ("arm-none-eabi-gcc", "cmake", "make")}
    problems = []
    if not tools["arm-none-eabi-gcc"]:
        problems.append("コンパイラ（arm-none-eabi-gcc）がありません")
    if not tools["cmake"]:
        problems.append("cmake がありません")
    if not tools["make"]:
        problems.append("make がありません")
    if not sdk:
        problems.append("Pico SDK が見つかりません（~/pico/pico-sdk か PICO_SDK_PATH）")
    elif not (sdk / "lib" / "tinyusb" / "src").is_dir():
        problems.append("Pico SDK のサブモジュールがありません（git submodule update --init）")
    version = ""
    if sdk:
        m = re.findall(r"set\(PICO_SDK_VERSION_(MAJOR|MINOR|REVISION) (\d+)\)",
                       _read(sdk / "pico_sdk_version.cmake"))
        version = ".".join(v for _, v in m)
    return {"ok": not problems, "problems": problems, "sdk": str(sdk) if sdk else None,
            "sdk_version": version, "project": str(PROJECT), "work": str(WORK), "home": str(Path.home())}


def _read(p):
    try:
        return Path(p).read_text()
    except OSError:
        return ""


# ---------- PC 側のファイル（~/apps/pico-cpp） ----------
def _project_file(name):
    if not NAME_RE.match(name or "") or not name.endswith(SOURCE_EXT):
        raise BuildError("ファイル名は英数字と . _ - だけで、.cpp / .h / .hpp / .c で終わる名前にしてください")
    return PROJECT / name


def list_files():
    if not PROJECT.is_dir():
        return []
    return [{"name": p.name, "size": p.stat().st_size, "dir": False}
            for p in sorted(PROJECT.iterdir()) if p.is_file() and p.suffix in SOURCE_EXT]


def read_file(name):
    return _project_file(name).read_text(encoding="utf-8", errors="replace")


def write_file(name, content):
    path = _project_file(name)
    first = not (PROJECT / "CMakeLists.txt").exists()
    PROJECT.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if first:
        init_project(PROJECT, quiet=True)      # 初めての保存なら、コマンドでもビルドできる形にしておく
    return str(path)


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
        put("blink.cpp", (SAMPLES / "02-blink.cpp").read_text(encoding="utf-8"))
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


def samples():
    out = []
    for p in sorted(SAMPLES.glob("*.cpp")):
        code = p.read_text(encoding="utf-8")
        first = code.splitlines()[0] if code else ""
        out.append({"name": first.lstrip("/ ").strip() or p.stem, "code": code})
    return out


# ---------- ビルドと書き込み ----------
class CppRunner:
    def __init__(self, console, pico, bootsel_state, flash_uf2):
        self.console = console
        self.pico = pico
        self.bootsel_state = bootsel_state
        self.flash_uf2 = flash_uf2
        self.busy = False
        self.stage = ""
        self.proc = None
        self.cancelled = False
        self.lock = threading.Lock()

    def log(self, text, kind="out"):
        self.console.add(text, kind)

    def start(self, code, board):
        if board not in BOARDS:
            raise BuildError(f"ボードの種類がわかりません: {board}")
        env = check_env()
        if not env["ok"]:
            raise BuildError("C++ の開発環境がそろっていません。\n・" + "\n・".join(env["problems"]) +
                             "\nガイド14章の「開発環境を用意する」を見てください。")
        with self.lock:
            if self.busy:
                raise BuildError("ビルド中です。終わるまで待つか「■ 停止」を押してください。")
            self.busy = True
            self.cancelled = False
        threading.Thread(target=self._worker, args=(code, board, Path(env["sdk"])), daemon=True).start()

    def cancel(self):
        self.cancelled = True
        p = self.proc
        if p and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except OSError:
                pass

    def _worker(self, code, board, sdk):
        try:
            self.stage = "build"
            uf2 = self.build(code, board, sdk)
            self.stage = "flash"
            self.flash(uf2)
            self.stage = "monitor"
            self.monitor()
        except BuildError as e:
            self.log(f"\n[エラー] {e}\n", "err")
        except Exception as e:  # noqa: BLE001
            self.log(f"\n[エラー] {type(e).__name__}: {e}\n", "err")
        finally:
            self.stage = ""
            self.busy = False

    # --- ビルド ---
    def prepare(self, code, sdk):
        (WORK / "app").mkdir(parents=True, exist_ok=True)
        inc = WORK / "include"
        if inc.exists():
            shutil.rmtree(inc)
        shutil.copytree(BUNDLED_INCLUDE, inc)
        shutil.copy(sdk / "external" / "pico_sdk_import.cmake", WORK / "pico_sdk_import.cmake")
        cm = CMAKE_TEMPLATE.format(project=PROJECT.as_posix(), libs=LIBRARIES)
        if _read(WORK / "CMakeLists.txt") != cm:
            (WORK / "CMakeLists.txt").write_text(cm)
        main = WORK / "app" / "main.cpp"
        if _read(main) != code:          # 変わっていなければ書かない（make がビルドし直さないように）
            main.write_text(code, encoding="utf-8")

    def build(self, code, board, sdk):
        self.prepare(code, sdk)
        bdir = WORK / f"build-{board}"
        env = dict(os.environ, PICO_SDK_PATH=str(sdk))
        t0 = time.time()
        self.log(f"\n[ビルド開始] ボード: {board}\n", "sys")
        if not (bdir / "Makefile").exists():
            self.log("[初回の準備（cmake）。数分かかることがあります]\n", "sys")
            self._run(["cmake", "-S", str(WORK), "-B", str(bdir), f"-DPICO_BOARD={board}",
                       f"-DPICO_SDK_PATH={sdk}"], env)
        self._run(["make", f"-j{os.cpu_count() or 2}", "app"], env, cwd=bdir, quiet=True)
        uf2 = bdir / "app.uf2"
        if not uf2.exists():
            raise BuildError("app.uf2 ができませんでした")
        size = (bdir / "app.bin").stat().st_size if (bdir / "app.bin").exists() else 0
        self.log(f"[ビルド完了] {time.time() - t0:.1f} 秒" +
                 (f"・プログラムの大きさ {size / 1024:.1f} KB" if size else "") + "\n", "sys")
        return uf2

    def _run(self, cmd, env, cwd=None, quiet=False):
        """コマンドを動かし、出力を流す。quiet なら進み具合の行は省き、警告とエラーだけ出す。"""
        if self.cancelled:
            raise BuildError("止めました")
        main = str(WORK / "app" / "main.cpp")
        self.proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, errors="replace",
                                     start_new_session=True)
        shown = []
        last_pct = ""
        for line in self.proc.stdout:
            line = line.replace(main, "main.cpp").replace(str(WORK) + "/", "")
            m = re.match(r"\[\s*(\d+)%\]", line)
            if quiet and m:
                if m.group(1) != last_pct and "app" in line and "Linking" in line:
                    self.log("  リンク中…\n", "sys")
                last_pct = m.group(1)
                continue
            if quiet and re.match(r"(make|gmake)\[\d+\]: (Entering|Leaving)", line):
                continue
            shown.append(line)
            kind = "err" if re.search(r"\b(error|エラー)\b|Error \d+|undefined reference", line) else "out"
            self.log(line, kind)
        code = self.proc.wait()
        self.proc.stdout.close()
        self.proc = None
        if self.cancelled:
            raise BuildError("止めました")
        if code != 0:
            raise BuildError("ビルドに失敗しました。上の「main.cpp:行:列: error:」の行を見てください。")

    # --- 書き込み ---
    def flash(self, uf2):
        st = self.bootsel_state()
        if not st["mount"]:
            self.log("[ピコを書き込みモードにします]\n", "sys")
            self.enter_bootsel()
            st = self.wait_mount(15)
        if not st["mount"]:
            raise BuildError("書き込みモードにできませんでした。ピコの BOOT を押しながら USB をつなぎ直して、"
                             "もう一度「▶ ビルドして書き込む」を押してください（ビルドは終わっているので、すぐ書き込みます）。")
        self.log(f"[書き込み中] {st['mount']}\n", "sys")
        self.flash_uf2(uf2.read_bytes())
        self.log("[書き込み完了。ピコが再起動します]\n", "sys")

    def enter_bootsel(self):
        port = self.pico.port
        was_python = self.pico.connected and self.pico.mode == "python"
        if was_python:
            try:                      # MicroPython の命令で書き込みモードにする
                self.pico.write(b"\r\x03\x03import machine\rmachine.bootloader()\r")
                time.sleep(0.3)
            except Exception:  # noqa: BLE001
                pass
        self.pico.disconnect()
        if self.wait_mount(4)["detected"]:
            return
        for p in [port] if port else pico_ports():
            try:                      # 1200 bps で開いて閉じると、SDK のプログラムは書き込みモードになる
                serial.Serial(p, 1200).close()
            except (serial.SerialException, OSError):
                pass
        if self.wait_mount(4)["detected"]:
            return
        for p in pico_ports():        # MicroPython が動いていて、まだつないでいなかった場合
            try:
                with serial.Serial(p, 115200, timeout=0.2) as s:
                    s.write(b"\r\x03\x03import machine\rmachine.bootloader()\r")
                    s.flush()
            except (serial.SerialException, OSError):
                pass

    def wait_mount(self, timeout):
        end = time.time() + timeout
        tried_mount = False
        while True:
            st = self.bootsel_state()
            if st["mount"] or self.cancelled:
                return st
            if st["detected"] and not tried_mount and time.time() > end - timeout + 3:
                tried_mount = True
                try_udisks_mount()
            if time.time() > end:
                return st
            time.sleep(0.3)

    # --- 出力を見る ---
    def monitor(self):
        end = time.time() + 15
        while time.time() < end and not self.cancelled:
            ports = pico_ports()
            if ports:
                time.sleep(0.5)       # ポートができてすぐは開けないことがある
                try:
                    self.pico.connect(ports[0], mode="cpp")
                    return
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(0.3)
        self.log("[ピコのシリアルポートが見つかりません。printf を使っていないプログラムなら問題ありません。"
                 "Pico W の LED など、動きを確かめてください]\n", "sys")


def pico_ports():
    import serial.tools.list_ports
    return sorted(p.device for p in serial.tools.list_ports.comports() if p.vid == 0x2E8A)


def try_udisks_mount():
    """ドライブが自動で開かれない PC のために、udisksctl で開いてみる。"""
    for label in ("RPI-RP2", "RP2350"):
        dev = Path("/dev/disk/by-label") / label
        if dev.exists() and shutil.which("udisksctl"):
            subprocess.run(["udisksctl", "mount", "-b", str(dev.resolve())],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        init_project(sys.argv[2] if len(sys.argv) > 2 else None)
    elif len(sys.argv) >= 2 and sys.argv[1] == "check":
        env = check_env()
        print("OK: C++ でビルドできます（Pico SDK " + env["sdk_version"] + "）" if env["ok"]
              else "足りないもの:\n・" + "\n・".join(env["problems"]))
        sys.exit(0 if env["ok"] else 1)
    else:
        print("使い方:\n  python3 cpp_build.py init [フォルダ]   プロジェクトのフォルダを作る（省略すると ~/apps/pico-cpp）\n"
              "  python3 cpp_build.py check            開発環境がそろっているか確かめる")
