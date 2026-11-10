#!/usr/bin/env python3
"""C++ モード（cpp_build.py）のテスト。

本物の Pico SDK とピコがなくても動くように、偽の cmake / make / SDK と、
偽の「書き込みモードのドライブ」を使う。

    python3 tests/test_cpp_mode.py
"""

import atexit
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="pico_cpp_test_"))
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
FAKE_SDK = TMP / "sdk"
FAKE_BIN = TMP / "bin"


def make_fakes():
    for d in ("lib/tinyusb/src", "external"):
        (FAKE_SDK / d).mkdir(parents=True, exist_ok=True)
    (FAKE_SDK / "pico_sdk_init.cmake").write_text("")
    (FAKE_SDK / "external" / "pico_sdk_import.cmake").write_text("# fake\n")
    (FAKE_SDK / "pico_sdk_version.cmake").write_text(
        "set(PICO_SDK_VERSION_MAJOR 2)\nset(PICO_SDK_VERSION_MINOR 1)\nset(PICO_SDK_VERSION_REVISION 1)\n")
    FAKE_BIN.mkdir(exist_ok=True)
    scripts = {
        "arm-none-eabi-gcc": "#!/bin/sh\nexit 0\n",
        # cmake -S src -B build ... → build/Makefile を作る
        "cmake": '#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = "-B" ] && B="$2"; shift; done\n'
                 'mkdir -p "$B" && echo "fake" > "$B/Makefile" && echo "-- Configuring done"\n',
        # make → main.cpp に BROKEN があればエラー、なければ app.uf2 を作る
        "make": '#!/bin/sh\nSRC="$(dirname "$PWD")/app/main.cpp"\n'
                'echo "[ 50%] Building CXX object CMakeFiles/app.dir/app/main.cpp.obj"\n'
                'if grep -q BROKEN "$SRC"; then echo "$SRC:3:5: error: \'BROKEN\' was not declared"; exit 2; fi\n'
                'echo "[100%] Linking CXX executable app.elf"\n'
                'printf "UF2\\nfake" > app.uf2; printf "12345678" > app.bin\n',
    }
    for name, body in scripts.items():
        p = FAKE_BIN / name
        p.write_text(body)
        p.chmod(0o755)


make_fakes()
os.environ["PICO_SDK_PATH"] = str(FAKE_SDK)
os.environ["PICO_STUDIO_WORK"] = str(TMP / "work")
os.environ["PICO_CPP_DIR"] = str(TMP / "project")
os.environ["PATH"] = f"{FAKE_BIN}:{os.environ['PATH']}"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cpp_build  # noqa: E402


class FakeConsole:
    def __init__(self):
        self.items = []

    def add(self, text, kind="out"):
        self.items.append((kind, text))

    def text(self, kind=None):
        return "".join(t for k, t in self.items if kind is None or k == kind)


class FakePico:
    def __init__(self, connected=False, mode="python", port=None):
        self._connected = connected
        self.mode = mode
        self.port = port
        self.written = []
        self.connected_to = None

    @property
    def connected(self):
        return self._connected

    def write(self, data):
        self.written.append(data)

    def disconnect(self):
        self._connected = False

    def connect(self, port, mode="python"):
        self.connected_to = (port, mode)
        self._connected = True
        self.mode = mode


class FakeDrive:
    """書き込みモードのドライブのまね。enter() が呼ばれるとドライブが出てくる。"""

    def __init__(self, mounted=False):
        self.mounted = mounted
        self.flashed = None

    def state(self):
        return {"detected": self.mounted, "mount": str(TMP / "RPI-RP2") if self.mounted else None}

    def flash(self, data):
        self.flashed = data
        return "firmware.uf2"


def run_and_wait(runner, code, board="pico", timeout=10):
    runner.start(code, board)
    end = time.time() + timeout
    while runner.busy and time.time() < end:
        time.sleep(0.05)
    assert not runner.busy, "終わりませんでした"


class CppModeTest(unittest.TestCase):
    def setUp(self):
        cpp_build.pico_ports = lambda: ["/dev/ttyACM9"]

    def test_env_ok(self):
        env = cpp_build.check_env()
        self.assertTrue(env["ok"], env["problems"])
        self.assertEqual(env["sdk_version"], "2.1.1")

    def test_env_missing_compiler(self):
        old = os.environ["PATH"]
        os.environ["PATH"] = "/nonexistent"
        try:
            env = cpp_build.check_env()
        finally:
            os.environ["PATH"] = old
        self.assertFalse(env["ok"])
        self.assertTrue(any("arm-none-eabi-gcc" in p for p in env["problems"]))

    def test_project_files(self):
        path = cpp_build.write_file("blink.cpp", "int main() {}\n")
        self.assertTrue(Path(path).exists())
        self.assertIn("blink.cpp", [f["name"] for f in cpp_build.list_files()])
        self.assertEqual(cpp_build.read_file("blink.cpp"), "int main() {}\n")
        for bad in ("../x.cpp", "a/b.cpp", "x.py", "", ".cpp/../.."):
            with self.assertRaises(cpp_build.BuildError, msg=bad):
                cpp_build.write_file(bad, "")
        cpp_build.delete_file("blink.cpp")
        self.assertNotIn("blink.cpp", [f["name"] for f in cpp_build.list_files()])

    def test_init_project(self):
        folder = TMP / "newproj"
        made = cpp_build.init_project(folder, quiet=True)
        for name in ("CMakeLists.txt", ".gitignore", "mpu6050.h", "ws2812.h", "blink.cpp", "pico_sdk_import.cmake"):
            self.assertIn(name, made)
        cm = (folder / "CMakeLists.txt").read_text()
        self.assertIn("file(GLOB APP_SOURCES", cm)
        self.assertIn("hardware_i2c", cm)
        self.assertIn("pico/pico-sdk", cm)                                    # PICO_SDK_PATH がなくても SDK を探す
        (folder / "CMakeLists.txt").write_text(cpp_build.project_cmake(fallback=False))
        self.assertTrue(cpp_build.init_project(folder, quiet=True)[0].startswith("CMakeLists.txt"))
        self.assertEqual((folder / "CMakeLists.txt").read_text(), cpp_build.project_cmake())
        (folder / "blink.cpp").write_text("// 自分で直した\n")
        self.assertEqual(cpp_build.init_project(folder, quiet=True), [])      # 2回目は何も上書きしない
        self.assertEqual((folder / "blink.cpp").read_text(), "// 自分で直した\n")

    def test_first_save_makes_project(self):
        project = Path(os.environ["PICO_CPP_DIR"])
        cpp_build.write_file("hello.cpp", "int main() {}\n")
        self.assertTrue((project / "CMakeLists.txt").exists())
        self.assertTrue((project / "mpu6050.h").exists())
        self.assertFalse((project / "blink.cpp").exists())                    # すでに .cpp があれば足さない

    def test_samples(self):
        names = [s["name"] for s in cpp_build.samples()]
        self.assertIn("LED を点滅させる", names)
        self.assertTrue(all(s["code"].count("int main") == 1 for s in cpp_build.samples()))

    def test_build_flash_monitor(self):
        console, pico, drive = FakeConsole(), FakePico(), FakeDrive(mounted=True)
        runner = cpp_build.CppRunner(console, pico, drive.state, drive.flash)
        run_and_wait(runner, "int main() { while (true) {} }\n", "pico2")
        self.assertEqual(console.text("err"), "")
        self.assertTrue(drive.flashed.startswith(b"UF2\n"))
        self.assertEqual(pico.connected_to, ("/dev/ttyACM9", "cpp"))
        work = Path(os.environ["PICO_STUDIO_WORK"])
        self.assertTrue((work / "build-pico2" / "Makefile").exists())
        self.assertIn("pico_stdlib", (work / "CMakeLists.txt").read_text())
        self.assertTrue((work / "include" / "mpu6050.h").exists())
        self.assertIn("ビルド完了", console.text("sys"))

    def test_build_error(self):
        console, pico, drive = FakeConsole(), FakePico(), FakeDrive(mounted=True)
        runner = cpp_build.CppRunner(console, pico, drive.state, drive.flash)
        run_and_wait(runner, "int main() {\n\n    BROKEN;\n}\n")
        self.assertIn("main.cpp:3:5: error", console.text("err"))
        self.assertNotIn(str(TMP), console.text())        # 作業フォルダの長い名前は出さない
        self.assertIsNone(drive.flashed)

    def test_enter_bootsel_from_micropython(self):
        console, drive = FakeConsole(), FakeDrive(mounted=False)
        pico = FakePico(connected=True, mode="python", port="/dev/ttyACM0")
        orig_write = pico.write

        def write(data):
            orig_write(data)
            if b"machine.bootloader()" in data:
                drive.mounted = True
        pico.write = write
        runner = cpp_build.CppRunner(console, pico, drive.state, drive.flash)
        run_and_wait(runner, "int main() {}\n")
        self.assertIsNotNone(drive.flashed, console.text())

    def test_enter_bootsel_by_1200bps(self):
        console, drive = FakeConsole(), FakeDrive(mounted=False)
        pico = FakePico(connected=True, mode="cpp", port="/dev/ttyACM0")
        opened = []

        class FakeSerial:
            def __init__(self, port, baud, **kw):
                opened.append((port, baud))
                if baud == 1200:
                    threading.Timer(0.2, lambda: setattr(drive, "mounted", True)).start()

            def close(self):
                pass

        old = cpp_build.serial.Serial
        cpp_build.serial.Serial = FakeSerial
        try:
            runner = cpp_build.CppRunner(console, pico, drive.state, drive.flash)
            run_and_wait(runner, "int main() {}\n", timeout=15)
        finally:
            cpp_build.serial.Serial = old
        self.assertIn(("/dev/ttyACM0", 1200), opened)
        self.assertIsNotNone(drive.flashed, console.text())

    def test_bad_board(self):
        runner = cpp_build.CppRunner(FakeConsole(), FakePico(), FakeDrive().state, FakeDrive().flash)
        with self.assertRaises(cpp_build.BuildError):
            runner.start("", "esp32")


if __name__ == "__main__":
    unittest.main(verbosity=2)
