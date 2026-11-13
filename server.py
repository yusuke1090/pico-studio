#!/usr/bin/env python3
"""Pico Studio: ラズパイピコがつながっているかを確かめ、MicroPython で手早く試すためのローカルサーバー。

C++ の開発は VS Code の拡張機能「Raspberry Pi Pico」で行い、ここでは出力の表示と開発環境の確認だけをする。

http://localhost:8765 を開いて使う。外部ライブラリは pyserial だけ。
"""

import argparse
import codecs
import glob
import json
import os
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import serial
import serial.tools.list_ports

import devenv

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}

RP_VID = 0x2E8A          # Raspberry Pi (RP2040 / RP2350)
MICROPYTHON_PID = 0x0005  # MicroPython の USB の番号。Pico SDK（C++）のプログラムは 0x000a など
BOOTSEL_PIDS = {0x0003, 0x000F}  # RP2040 / RP2350 の BOOTSEL モード
RAW_BANNER = b"raw REPL; CTRL-B to exit\r\n>"
FIRMWARE_PAGE = "https://micropython.org/download/RPI_PICO/"



class DeviceError(Exception):
    pass


class Console:
    """ブラウザに表示するログ。seq 番号つきで追記していく。"""

    def __init__(self, limit=4000):
        self.lock = threading.Lock()
        self.items = []
        self.seq = 0
        self.limit = limit

    def add(self, text, kind="out"):
        if not text:
            return
        with self.lock:
            self.seq += 1
            self.items.append({"seq": self.seq, "text": text, "kind": kind})
            if len(self.items) > self.limit:
                del self.items[: len(self.items) - self.limit]

    def since(self, n):
        with self.lock:
            return [i for i in self.items if i["seq"] > n], self.seq


class Pico:
    """シリアルポート越しに MicroPython の REPL を操作する。"""

    def __init__(self, console):
        self.console = console
        self.ser = None
        self.port = None
        self.reader = None
        self.alive = False
        self.raw = False             # True の間、受信データを rx に溜めて解析する
        self.rx = bytearray()
        self.cond = threading.Condition()
        self.write_lock = threading.Lock()
        self.op_lock = threading.Lock()  # 実行・ファイル操作は同時に1つだけ
        self.running = False
        self.mode = "python"         # "python" = MicroPython の REPL、"cpp" = C++ の出力を表示するだけ
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")

    # ---------- 接続 ----------
    @property
    def connected(self):
        return self.ser is not None and self.alive

    def connect(self, port, mode="python"):
        self.disconnect()
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.05)
        except serial.SerialException as e:
            self.ser = None
            msg = str(e)
            if "Permission denied" in msg:
                msg = ("ポートを開く権限がありません。ガイド0章の「『ポートを開く権限がありません』と出たとき」"
                       "（README の「権限の設定」にも同じ内容）を見て、udev ルールを入れてください。")
            raise DeviceError(msg)
        self.port = port
        self.mode = mode
        self.alive = True
        self.raw = False
        self.decoder.reset()
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()
        if mode == "cpp":
            self.console.add(f"[{port} に接続しました（C++ のプログラムの出力を表示します）]\n", "sys")
            return
        self.console.add(f"[{port} に接続しました]\n", "sys")
        # 動いているプログラムを止めて、プロンプトを出してもらう
        self.write(b"\r\x03\x03")

    def disconnect(self):
        if self.ser is None:
            return
        self.alive = False
        try:
            self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.running = False
        with self.cond:
            self.cond.notify_all()
        self.console.add(f"[{self.port} から切断しました]\n", "sys")
        self.port = None

    def write(self, data):
        if not self.connected:
            raise DeviceError("ピコに接続していません")
        with self.write_lock:
            try:
                self.ser.write(data)
                self.ser.flush()
            except serial.SerialException as e:
                self._lost(e)
                raise DeviceError(f"送信に失敗しました: {e}")

    def _lost(self, err):
        if self.alive:
            self.console.add(f"\n[接続が切れました: {err}]\n", "err")
        self.disconnect()

    def _read_loop(self):
        while self.alive:
            try:
                n = self.ser.in_waiting
                data = self.ser.read(n or 1)
            except (serial.SerialException, OSError, TypeError, AttributeError) as e:
                self._lost(e)
                return
            if not data:
                continue
            if self.raw:
                with self.cond:
                    self.rx += data
                    self.cond.notify_all()
            else:
                self.console.add(self.decoder.decode(data), "out")

    # ---------- raw REPL ----------
    def _take(self):
        with self.cond:
            data = bytes(self.rx)
            self.rx.clear()
            return data

    def _wait_for(self, marker, timeout):
        """rx に marker が来るまで待ち、marker までを取り出して返す。"""
        end = time.time() + timeout
        with self.cond:
            while True:
                i = self.rx.find(marker)
                if i >= 0:
                    got = bytes(self.rx[: i + len(marker)])
                    del self.rx[: i + len(marker)]
                    return got
                left = end - time.time()
                if left <= 0 or not self.alive:
                    raise DeviceError(
                        "ピコから応答がありません。MicroPython が書き込まれているか確認してください。")
                self.cond.wait(left)

    def _enter_raw(self):
        self.raw = True
        self.write(b"\r\x03\x03")
        time.sleep(0.15)
        self._take()
        for _ in range(2):
            self.write(b"\r\x01")
            try:
                self._wait_for(RAW_BANNER, 1.5)
                return
            except DeviceError:
                self.write(b"\x03\x03")
                time.sleep(0.2)
                self._take()
        raise DeviceError(
            "MicroPython の応答がありません。MicroPython が書き込まれているか、"
            "別のソフト（Thonny や mpremote）がポートを使っていないか確認してください。")

    def _leave_raw(self, prompt=False):
        try:
            if self.connected:
                self.write(b"\x02")
                try:
                    self._wait_for(b">>> ", 1.0)
                except DeviceError:
                    pass
        finally:
            self._take()
            self.raw = False
        if prompt:
            self.console.add(">>> ", "out")

    def _send_code(self, code):
        data = code.encode("utf-8")
        for i in range(0, len(data), 256):
            self.write(data[i:i + 256])
            time.sleep(0.01)
        self.write(b"\x04")
        resp = self._wait_for(b"OK", 3.0)
        if not resp.endswith(b"OK"):
            raise DeviceError("コードを受け取ってもらえませんでした")

    def _stream_until_eot(self, on_text, timeout=None):
        """\\x04 が来るまでの受信データを on_text に渡し続ける。"""
        dec = codecs.getincrementaldecoder("utf-8")("replace")
        end = None if timeout is None else time.time() + timeout
        while True:
            with self.cond:
                if not self.rx:
                    if not self.alive:
                        raise DeviceError("接続が切れました")
                    if end is not None and time.time() > end:
                        raise DeviceError("タイムアウトしました")
                    self.cond.wait(0.2)
                    continue
                i = self.rx.find(b"\x04")
                if i >= 0:
                    chunk = bytes(self.rx[:i])
                    del self.rx[: i + 1]
                else:
                    chunk = bytes(self.rx)
                    self.rx.clear()
            on_text(dec.decode(chunk))
            if i >= 0:
                on_text(dec.decode(b"", final=True))
                return

    def _need_python(self):
        if self.mode != "python":
            raise DeviceError("このピコでは C++ のプログラムが動いています（出力の表示だけできます）。"
                              "MicroPython で試すときは、BOOT を押しながらつなぎ、MicroPython を書き込んでください。")

    def exec_capture(self, code, timeout=10):
        """コードを実行して、出力を文字列で返す（コンソールには出さない）。"""
        self._need_python()
        if not self.op_lock.acquire(blocking=False):
            raise DeviceError("プログラムの実行中です。停止してから操作してください。")
        try:
            out, err = [], []
            self._enter_raw()
            try:
                self._send_code(code)
                self._stream_until_eot(out.append, timeout)
                self._stream_until_eot(err.append, timeout)
            finally:
                self._leave_raw()
            if "".join(err).strip():
                raise DeviceError("".join(err).strip())
            return "".join(out)
        finally:
            self.op_lock.release()

    def run(self, code):
        """コードをバックグラウンドで実行し、出力をコンソールに流す。"""
        if not self.connected:
            raise DeviceError("ピコに接続していません")
        self._need_python()
        if not self.op_lock.acquire(blocking=False):
            raise DeviceError("すでにプログラムを実行中です")

        def worker():
            self.running = True
            try:
                self.console.add("\n[実行開始]\n", "sys")
                self._enter_raw()
                try:
                    self._send_code(code)
                    self._stream_until_eot(lambda t: self.console.add(t, "out"))
                    self._stream_until_eot(lambda t: self.console.add(t, "err"))
                finally:
                    self._leave_raw()
                self.console.add("\n[実行終了]\n", "sys")
                self.console.add(">>> ", "out")
            except DeviceError as e:
                self.raw = False
                self.console.add(f"\n[エラー] {e}\n", "err")
            finally:
                self.running = False
                self.op_lock.release()

        threading.Thread(target=worker, daemon=True).start()

    def stop(self):
        self.write(b"\x03")

    def send_line(self, text):
        self.write(text.encode("utf-8") + (b"\r\n" if self.mode == "cpp" else b"\r"))

    def soft_reset(self):
        self._need_python()
        if self.running:
            raise DeviceError("プログラムの実行中です。停止してからリセットしてください。")
        self.console.add("\n[ソフトリセット（main.py があれば実行されます）]\n", "sys")
        self.write(b"\x03\x04")

    # ---------- ファイル操作 ----------
    def info(self):
        out = self.exec_capture(
            "import sys,os,gc\n"
            "u=os.uname()\n"
            "s=os.statvfs('/')\n"
            "gc.collect()\n"
            "print(u.machine)\nprint(u.release)\n"
            "print(s[0]*s[3])\nprint(s[0]*s[2])\nprint(gc.mem_free())\n")
        lines = out.strip().splitlines()
        if len(lines) < 5:
            raise DeviceError("ボード情報を取得できませんでした: " + out)
        return {"machine": lines[0], "version": lines[1],
                "flash_free": int(lines[2]), "flash_total": int(lines[3]),
                "mem_free": int(lines[4])}

    def list_files(self):
        out = self.exec_capture(
            "import os\n"
            "def _w(p):\n"
            " for e in os.ilistdir(p):\n"
            "  n=e[0];t=e[1];f=(p+'/'+n) if p!='/' else '/'+n\n"
            "  if t==0x4000:\n"
            "   print('D',f);_w(f)\n"
            "  else:\n"
            "   print('F',os.stat(f)[6],f)\n"
            "_w('/')\n")
        files = []
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if parts[0] == "D" and len(parts) == 2:
                files.append({"name": parts[1], "dir": True, "size": 0})
            elif parts[0] == "F" and len(parts) == 3:
                files.append({"name": parts[2], "dir": False, "size": int(parts[1])})
        return files

    def read_file(self, name):
        out = self.exec_capture(
            "import ubinascii\n"
            f"with open({name!r},'rb') as f:\n"
            " while True:\n"
            "  b=f.read(512)\n"
            "  if not b: break\n"
            "  print(ubinascii.b2a_base64(b).decode(),end='')\n", timeout=30)
        import base64
        data = b"".join(base64.b64decode(l) for l in out.split() if l)
        return data.decode("utf-8", "replace")

    def write_file(self, name, content):
        data = content.encode("utf-8")
        lines = [f"f=open({name!r},'wb')", "w=f.write"]
        for i in range(0, len(data), 256):
            lines.append(f"w({data[i:i + 256]!r})")
        lines.append("f.close()")
        self.exec_capture("\n".join(lines) + "\n", timeout=30)

    def delete_file(self, name):
        self.exec_capture(f"import os\nos.remove({name!r})\n")


# ---------- USB / BOOTSEL ----------
def list_ports():
    ports = []
    for p in serial.tools.list_ports.comports():
        if not p.device.startswith(("/dev/ttyACM", "/dev/ttyUSB")) and p.vid is None:
            continue
        ports.append({
            "device": p.device,
            "description": p.description or "",
            "vid": p.vid, "pid": p.pid,
            "is_pico": p.vid == RP_VID,
            "kind": ("micropython" if p.pid == MICROPYTHON_PID else "cpp") if p.vid == RP_VID else "other",
        })
    ports.sort(key=lambda p: (not p["is_pico"], p["device"]))
    return ports


def port_kind_mode(device):
    """ポートのピコで動いているものから、つなぎ方を決める（MicroPython なら REPL、C++ なら出力を表示するだけ）"""
    for p in list_ports():
        if p["device"] == device and p["kind"] == "cpp":
            return "cpp"
    return "python"


def bootsel_state():
    detected = False
    for d in glob.glob("/sys/bus/usb/devices/*"):
        try:
            vid = int(Path(d, "idVendor").read_text().strip(), 16)
            pid = int(Path(d, "idProduct").read_text().strip(), 16)
        except (OSError, ValueError):
            continue
        if vid == RP_VID and pid in BOOTSEL_PIDS:
            detected = True
    mount = None
    try:
        for line in Path("/proc/mounts").read_text().splitlines():
            target = line.split()[1].replace("\\040", " ")
            if os.path.basename(target) in ("RPI-RP2", "RP2350") and \
                    Path(target, "INFO_UF2.TXT").exists():
                mount = target
    except OSError:
        pass
    return {"detected": detected or mount is not None, "mount": mount}


def latest_firmware_url():
    req = urllib.request.Request(FIRMWARE_PAGE, headers={"User-Agent": "pico-studio"})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8", "replace")
    for href in re.findall(r'href="([^"]+\.uf2)"', html):
        if "preview" in href:
            continue
        return urllib.request.urljoin(FIRMWARE_PAGE, href)
    raise DeviceError("最新のファームウェアが見つかりませんでした")


def flash_uf2(data):
    st = bootsel_state()
    if not st["mount"]:
        raise DeviceError("RPI-RP2 ドライブが見つかりません。BOOT ボタンを押しながら USB をつないでください。")
    if not data.startswith(b"UF2\n"):
        raise DeviceError("UF2 ファイルではありません")
    dest = Path(st["mount"], "firmware.uf2")
    with open(dest, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return str(dest)


# ---------- HTTP ----------
console = Console()
pico = Pico(console)


class Handler(BaseHTTPRequestHandler):
    server_version = "PicoStudio/1.0"

    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path):
        body = path.read_bytes()
        ctype = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _check_origin(self):
        # 他のサイトから勝手に操作されないように、同じホストからのリクエストだけ受け付ける
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        host = self.headers.get("Host", "")
        return urlparse(origin).netloc == host

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        try:
            if url.path in ("/", "/index.html"):
                self._file(STATIC / "index.html")
            elif url.path == "/api/state":
                items, last = console.since(int(q.get("since", ["0"])[0]))
                self._json({"connected": pico.connected, "port": pico.port, "mode": pico.mode,
                            "running": pico.running,
                            "console": items, "last": last})
            elif url.path == "/api/ports":
                self._json({"ports": list_ports(), "bootsel": bootsel_state()})
            elif url.path == "/api/info":
                self._json(pico.info())
            elif url.path == "/api/files":
                self._json({"files": pico.list_files()})
            elif url.path == "/api/file":
                self._json({"content": pico.read_file(q["name"][0])})
            elif url.path == "/api/env":
                self._json(devenv.check())
            else:
                self._json({"error": "not found"}, 404)
        except DeviceError as e:
            self._json({"error": str(e)}, 409)
        except FileNotFoundError as e:
            self._json({"error": f"ファイルがありません: {e.filename}"}, 404)
        except Exception as e:  # noqa: BLE001
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        if not self._check_origin():
            return self._json({"error": "forbidden"}, 403)
        url = urlparse(self.path)
        try:
            if url.path == "/api/flash":
                dest = flash_uf2(self._body())
                return self._json({"ok": True, "dest": dest})
            if url.path == "/api/flash-latest":
                fw_url = latest_firmware_url()
                with urllib.request.urlopen(fw_url, timeout=60) as r:
                    data = r.read()
                dest = flash_uf2(data)
                return self._json({"ok": True, "dest": dest, "url": fw_url})

            body = json.loads(self._body() or b"{}")
            if url.path == "/api/connect":
                pico.connect(body["port"], body.get("mode") or port_kind_mode(body["port"]))
            elif url.path == "/api/disconnect":
                pico.disconnect()
            elif url.path == "/api/run":
                pico.run(body["code"])
            elif url.path == "/api/stop":
                pico.stop()
            elif url.path == "/api/send":
                pico.send_line(body["text"])
            elif url.path == "/api/reset":
                pico.soft_reset()
            elif url.path == "/api/file":
                pico.write_file(body["name"], body["content"])
            elif url.path == "/api/delete":
                pico.delete_file(body["name"])
            elif url.path == "/api/clear":
                with console.lock:
                    console.items.clear()
            else:
                return self._json({"error": "not found"}, 404)
            self._json({"ok": True})
        except DeviceError as e:
            self._json({"error": str(e)}, 409)
        except FileNotFoundError as e:
            self._json({"error": f"ファイルがありません: {e.filename}"}, 404)
        except ValueError as e:
            self._json({"error": str(e)}, 400)
        except Exception as e:  # noqa: BLE001
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)


def main():
    ap = argparse.ArgumentParser(description="Pico Studio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        if e.errno == 98:
            raise SystemExit(
                f"ポート {args.port} はすでに使われています。\n"
                f"Pico Studio がもう起動していれば http://localhost:{args.port} を開いてください。\n"
                f"別のポートで起動するには: python3 server.py --port 9000")
        raise
    print(f"Pico Studio: http://localhost:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        pico.disconnect()


if __name__ == "__main__":
    main()
