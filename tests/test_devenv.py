#!/usr/bin/env python3
"""devenv.py（C++ の開発環境の確認とプロジェクトの用意）と、接続のしかたの自動判定のテスト。

本物の VS Code・SDK がなくても動くように、偽のホームフォルダを使う。

    python3 tests/test_devenv.py
"""

import atexit
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="pico_devenv_test_"))
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
HOME = TMP / "home"
HOME.mkdir()
os.environ["HOME"] = str(HOME)
os.environ.pop("PICO_SDK_PATH", None)
(TMP / "emptybin").mkdir()
os.environ["PATH"] = str(TMP / "emptybin")     # PC に入っているコンパイラや picotool を見ないように
os.environ["PICO_CPP_DIR"] = str(TMP / "project")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import devenv  # noqa: E402


def fake_vscode_install():
    """VS Code の拡張機能と、拡張機能が ~/.pico-sdk に入れるものをまねる"""
    (HOME / ".vscode/extensions/raspberry-pi.raspberry-pi-pico-0.23.0").mkdir(parents=True)
    for ver in ("2.0.0", "2.1.1"):
        sdk = HOME / ".pico-sdk/sdk" / ver
        (sdk / "external").mkdir(parents=True)
        (sdk / "pico_sdk_init.cmake").write_text("")
        (sdk / "external/pico_sdk_import.cmake").write_text("# fake\n")
        major, minor, rev = ver.split(".")
        (sdk / "pico_sdk_version.cmake").write_text(
            f"set(PICO_SDK_VERSION_MAJOR {major})\nset(PICO_SDK_VERSION_MINOR {minor})\nset(PICO_SDK_VERSION_REVISION {rev})\n")
    gcc = HOME / ".pico-sdk/toolchain/14_2_Rel1/bin/arm-none-eabi-gcc"
    gcc.parent.mkdir(parents=True)
    gcc.write_text("#!/bin/sh\n")
    gcc.chmod(0o755)
    pt = HOME / ".pico-sdk/picotool/2.1.1/picotool/picotool"
    pt.parent.mkdir(parents=True)
    pt.write_text("#!/bin/sh\necho 'picotool v2.1.1 (Linux, GNU-14.2.0, Release)'\n")
    pt.chmod(0o755)


class DevenvTest(unittest.TestCase):
    def test_1_nothing_installed(self):
        env = devenv.check()
        self.assertFalse(env["ok"])
        self.assertIsNone(env["items"]["vscode"])
        self.assertTrue(any("VS Code" in p for p in env["problems"]))

    def test_2_vscode_extension_install(self):
        fake_vscode_install()
        env = devenv.check()
        self.assertTrue(env["ok"], env["problems"])
        self.assertEqual(env["items"]["vscode"], "0.23.0")
        self.assertEqual(env["sdk_version"], "2.1.1")                  # 新しいほうを選ぶ
        self.assertTrue(env["items"]["compiler"].endswith("14_2_Rel1/bin/arm-none-eabi-gcc"))
        self.assertTrue(env["items"]["picotool"].endswith("picotool/picotool"))

    def test_3_init_project(self):
        folder = TMP / "newproj"
        made = devenv.init_project(folder, quiet=True)
        for name in ("CMakeLists.txt", ".gitignore", "mpu6050.h", "ws2812.h", "blink.cpp", "pico_sdk_import.cmake"):
            self.assertIn(name, made)
        cm = (folder / "CMakeLists.txt").read_text()
        self.assertIn("file(GLOB APP_SOURCES", cm)
        self.assertIn("pico/pico-sdk", cm)
        self.assertIn('printf("LED %s\\n"', (folder / "blink.cpp").read_text())
        (folder / "blink.cpp").write_text("// 自分で直した\n")
        self.assertEqual(devenv.init_project(folder, quiet=True), [])      # 2回目は何も上書きしない
        self.assertEqual((folder / "blink.cpp").read_text(), "// 自分で直した\n")
        (folder / "CMakeLists.txt").write_text(devenv.project_cmake(fallback=False))
        self.assertTrue(devenv.init_project(folder, quiet=True)[0].startswith("CMakeLists.txt"))


class ConnectModeTest(unittest.TestCase):
    def test_mode_from_usb_id(self):
        import server
        server.list_ports = lambda: [
            {"device": "/dev/ttyACM0", "kind": "micropython"},
            {"device": "/dev/ttyACM1", "kind": "cpp"},
        ]
        self.assertEqual(server.port_kind_mode("/dev/ttyACM0"), "python")
        self.assertEqual(server.port_kind_mode("/dev/ttyACM1"), "cpp")
        self.assertEqual(server.port_kind_mode("/dev/pts/3"), "python")   # わからなければ MicroPython として試す


if __name__ == "__main__":
    unittest.main(verbosity=2)
