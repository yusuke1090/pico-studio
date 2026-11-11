#!/usr/bin/env python3
"""ガイドの付箋・線・メモを保存する API（/api/notes）のテスト。

保存先は一時フォルダにする（本物の ~/.local/share/pico-studio には触らない）。

    python3 tests/test_notes.py
"""

import atexit
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="pico_notes_test_"))
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["XDG_DATA_HOME"] = str(TMP)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402

NOTES = TMP / "pico-studio/notes.json"


def item(i, **kw):
    return {"id": f"m{i}", "type": "mark", "file": "03-vscode.md", "color": "yellow", "note": "",
            "exact": "1つのフォルダ", "prefix": "", "suffix": "", "pos": 0, "created": "2026-11-11T12:00:00Z", **kw}


class NotesApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        shutil.rmtree(TMP / "pico-studio", ignore_errors=True)

    def request(self, path, body=None, origin=None):
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        req = urllib.request.Request(self.base + path, data=data)
        if origin:
            req.add_header("Origin", origin)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read())

    def test_empty_at_first(self):
        status, j = self.request("/api/notes")
        self.assertEqual(status, 200)
        self.assertEqual(j["items"], [])
        self.assertTrue(j["path"].endswith("pico-studio/notes.json"))

    def test_save_and_load(self):
        items = [item(1), item(2, type="sticky", note="ここまで読んだ", color="pink")]
        self.assertEqual(self.request("/api/notes", {"items": items}), (200, {"ok": True}))
        self.assertEqual(self.request("/api/notes")[1]["items"], items)
        self.assertEqual(json.loads(NOTES.read_text())["items"], items)

    def test_keeps_previous_version(self):
        self.request("/api/notes", {"items": [item(1)]})
        self.request("/api/notes", {"items": []})
        self.assertEqual(json.loads(NOTES.with_suffix(".json.bak").read_text())["items"], [item(1)])
        self.assertEqual(self.request("/api/notes")[1]["items"], [])

    def test_rejects_wrong_shape(self):
        for body in ({"items": "x"}, {"items": [{"id": "a"}]}, {"items": [item(1, type="other")]}, {}):
            status, j = self.request("/api/notes", body)
            self.assertEqual(status, 400, body)
            self.assertIn("error", j)
        self.assertFalse(NOTES.exists())

    def test_rejects_too_big(self):
        status, _ = self.request("/api/notes", {"items": [item(1, note="あ" * 1_000_000)]})
        self.assertEqual(status, 400)

    def test_rejects_other_sites(self):
        status, _ = self.request("/api/notes", {"items": [item(1)]}, origin="https://example.com")
        self.assertEqual(status, 403)
        self.assertFalse(NOTES.exists())

    def test_beacon_text_body(self):
        # タブを閉じるときの sendBeacon は text/plain で送られる
        status, _ = self.request("/api/notes", json.dumps({"items": [item(3)]}).encode())
        self.assertEqual(status, 200)
        self.assertEqual(self.request("/api/notes")[1]["items"][0]["id"], "m3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
