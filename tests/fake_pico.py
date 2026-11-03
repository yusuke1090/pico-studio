#!/usr/bin/env python3
"""テスト用の「偽のピコ」。

疑似端末 (pty) を作って、MicroPython の REPL / raw REPL のやり取りをまねる。
ピコを持っていなくても Pico Studio の動作を確かめられる。

    python3 tests/fake_pico.py
    # 表示されたポート (/dev/pts/N) を Pico Studio のポート欄で選ぶ
"""

import builtins
import contextlib
import io
import os
import sys
import tempfile
import tty
import types

ROOT = tempfile.mkdtemp(prefix="fake_pico_")


def real(p):
    return os.path.join(ROOT, p.lstrip("/"))


def make_namespace(fd):
    """MicroPython にしかない関数を CPython で用意する。"""
    import binascii
    import gc

    fake_os = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("_")})
    fake_os.uname = lambda: types.SimpleNamespace(
        machine="Fake Pico with RP2040", release="1.99.0-fake")
    fake_os.statvfs = lambda p: (4096, 4096, 512, 400, 400, 0, 0, 0, 0, 255)
    fake_os.ilistdir = lambda p: [
        (n, 0x4000 if os.path.isdir(os.path.join(real(p), n)) else 0x8000, 0, 0)
        for n in sorted(os.listdir(real(p)))]
    fake_os.stat = lambda p: os.stat(real(p))
    fake_os.remove = lambda p: os.remove(real(p))
    fake_os.listdir = lambda p="/": os.listdir(real(p))

    fake_gc = types.SimpleNamespace(collect=gc.collect, mem_free=lambda: 180000)

    def fake_open(p, mode="r", *a, **k):
        return builtins.open(real(p), mode, *a, **k)

    def fake_input(prompt=""):
        out = os.fdopen(os.dup(fd), "w")
        out.write(prompt)
        out.flush()
        line = b""
        while True:
            c = os.read(fd, 1)
            if c == b"\x03":
                raise KeyboardInterrupt
            if c in (b"\r", b"\n"):
                os.write(fd, b"\r\n")
                return line.decode()
            os.write(fd, c)
            line += c

    mods = {"os": fake_os, "gc": fake_gc, "ubinascii": binascii}
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        return mods[name] if name in mods else real_import(name, *a, **k)

    b = dict(vars(builtins))
    b.update(open=fake_open, input=fake_input, __import__=fake_import)
    return {"__builtins__": b, "__name__": "__main__"}


class FdWriter(io.TextIOBase):
    def __init__(self, fd):
        self.fd = fd

    def write(self, s):
        os.write(self.fd, s.replace("\n", "\r\n").encode())
        return len(s)


def run_code(fd, code):
    """コードを実行し (stdout, エラー文字列) を返す。Ctrl-C で止められる。"""
    ns = make_namespace(fd)
    err = ""
    w = FdWriter(fd)
    with contextlib.redirect_stdout(w):
        try:
            exec(compile(code, "<stdin>", "exec"), ns)
        except KeyboardInterrupt:
            err = "Traceback (most recent call last):\r\nKeyboardInterrupt: \r\n"
        except Exception as e:  # noqa: BLE001
            err = f"Traceback (most recent call last):\r\n{type(e).__name__}: {e}\r\n"
    return err


def main():
    master, slave = os.openpty()
    tty.setraw(slave)
    print(os.ttyname(slave), flush=True)
    print(f"(fake filesystem: {ROOT})", file=sys.stderr, flush=True)
    fd = master
    raw = False
    buf = b""

    def friendly_banner():
        os.write(fd, b"MicroPython v1.99.0-fake; Fake Pico with RP2040\r\n"
                     b"Type \"help()\" for more information.\r\n>>> ")

    while True:
        c = os.read(fd, 1)
        if not raw:
            if c == b"\x01":
                raw = True
                buf = b""
                os.write(fd, b"raw REPL; CTRL-B to exit\r\n>")
            elif c == b"\x03":
                os.write(fd, b"\r\n>>> ")
            elif c == b"\x04":
                os.write(fd, b"MPY: soft reboot\r\n")
                friendly_banner()
            elif c == b"\r":
                line, buf = buf.decode(), b""
                os.write(fd, b"\r\n")
                if line.strip():
                    err = run_code(fd, line)
                    os.write(fd, err.encode())
                os.write(fd, b">>> ")
            else:
                buf += c
                os.write(fd, c)
        else:
            if c == b"\x02":
                raw = False
                os.write(fd, b"\r\n")
                friendly_banner()
            elif c == b"\x01":
                buf = b""
                os.write(fd, b"\r\n>")
            elif c == b"\x03":
                buf = b""
            elif c == b"\x04":
                code, buf = buf.decode(), b""
                os.write(fd, b"OK")
                err = run_code(fd, code)
                os.write(fd, b"\x04" + err.encode() + b"\x04>")
            else:
                buf += c


if __name__ == "__main__":
    main()
