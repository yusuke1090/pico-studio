#!/usr/bin/env python3
"""ガイドの C++ のプログラムを、本物の Pico SDK で全部ビルドして確かめる。

guide/*.md の ```cpp run のブロック（そのままビルドできる1つのプログラム）を取り出し、
1つのプロジェクトにまとめてビルドする。エラーと警告は、ガイドのファイルと行に直して表示する。
17章の PC 用テスト（features.h と test_features.cpp）と、11章の filter.h も PC の g++ で確かめる。

    python3 tests/build_guide_cpp.py              # Pico（RP2040）でビルド
    python3 tests/build_guide_cpp.py pico pico2   # Pico と Pico 2 の両方

Pico SDK とコンパイラが必要（python3 devenv.py check）。作業フォルダは ~/.cache/pico-studio/guide-check。
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import devenv  # noqa: E402

WORK = Path.home() / ".cache" / "pico-studio" / "guide-check"
DIAG = re.compile(r"(?P<file>[\w./-]+\.(?:cpp|h)):(?P<line>\d+):(?P<col>\d+): (?P<kind>error|warning): (?P<msg>.*)")


def blocks(md_path, lang_flag):
    text = md_path.read_text(encoding="utf-8")
    for m in re.finditer(rf"^```{lang_flag}\n(.*?)^```", text, re.S | re.M):
        yield text[:m.start()].count("\n") + 1, m.group(1)


def prepare():
    """プログラムを取り出して、作業フォルダに1つのプロジェクトを作る。{ファイル名: (ガイドの md, 行)} を返す"""
    WORK.mkdir(parents=True, exist_ok=True)
    for old in WORK.glob("ch*.cpp"):
        old.unlink()
    where = {}
    for md in sorted((ROOT / "guide").glob("*.md")):
        ch = md.name.split("-")[0]
        for k, (line, code) in enumerate(blocks(md, "cpp run"), 1):
            name = f"ch{ch}_{k}.cpp"
            (WORK / name).write_text(code, encoding="utf-8")
            where[name] = (md.relative_to(ROOT), line)
    for h in (ROOT / "cpp" / "include").glob("*.h"):
        shutil.copy(h, WORK)
    # 14章の model.h の例（```text のブロック）
    ml = (ROOT / "guide" / "14-ml.md").read_text(encoding="utf-8")
    m = re.search(r"^```text\n(// train.py で自動生成した決定木.*?)^```", ml, re.S | re.M)
    (WORK / "model.h").write_text(m.group(1), encoding="utf-8")
    cm = devenv.project_cmake().replace(
        '    add_executable(${name} "${src}")',
        '    add_executable(${name} "${src}")\n'
        '    set_source_files_properties("${src}" PROPERTIES COMPILE_OPTIONS "-Wall;-Wextra")')
    (WORK / "CMakeLists.txt").write_text(cm, encoding="utf-8")
    shutil.copy(devenv.sdk_path() / "external" / "pico_sdk_import.cmake", WORK)
    return where


def build(board, where):
    bdir = WORK / f"build-{board}"
    env = dict(os.environ, PICO_SDK_PATH=str(devenv.sdk_path()))
    print(f"\n== {board}: 設定（cmake）")
    r = subprocess.run(["cmake", "-S", str(WORK), "-B", str(bdir), f"-DPICO_BOARD={board}"],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return 1
    print(f"== {board}: ビルド（{len(where)} 個のプログラム。初回は数分かかる）")
    r = subprocess.run(["make", "-C", str(bdir), "-k", f"-j{os.cpu_count() or 2}"],
                       env=env, capture_output=True, text=True)
    problems = 0
    seen = set()
    for line in (r.stdout + r.stderr).splitlines():
        d = DIAG.search(line)
        if not d:
            continue
        f = Path(d["file"])
        if WORK not in f.parents and f.parent != WORK:
            continue                                # SDK の中の警告は見ない
        key = (f.name, d["line"], d["msg"])
        if key in seen:
            continue
        seen.add(key)
        problems += 1
        if f.name in where:
            md, start = where[f.name]
            place = f"{md}:{start + int(d['line'])}"
        else:
            place = f"{f.name}:{d['line']}（cpp/include のヘッダー）"
        print(f"  {d['kind']}: {place}: {d['msg']}")
    built = len(list(bdir.glob("ch*.uf2")))
    print(f"== {board}: {built} / {len(where)} 個ビルドできた。エラーと警告: {problems} 件")
    return problems + (len(where) - built)


def pc_tests():
    """17章の PC 用テストと、11章の filter.h を g++ で確かめる"""
    if not shutil.which("g++"):
        print("\n== PC のテスト: g++ がないので飛ばす")
        return 0
    t = WORK / "pc"
    t.mkdir(exist_ok=True)
    shutil.copy(WORK / "model.h", t)
    prod = [c for _, c in blocks(ROOT / "guide" / "17-product.md", "cpp")]
    (t / "features.h").write_text(next(c for c in prod if "inline void features" in c), encoding="utf-8")
    (t / "test_features.cpp").write_text(next(c for c in prod if "assert(" in c), encoding="utf-8")
    style = [c for _, c in blocks(ROOT / "guide" / "11-cpp-style.md", "cpp")]
    (t / "filter.h").write_text(next(c for c in style if "MovingAverage" in c), encoding="utf-8")
    (t / "t_filter.cpp").write_text(
        '#include <cassert>\n#include <initializer_list>\n#include "filter.h"\n'
        'int main() { MovingAverage<3> m; float r = 0; for (float v : {3.f, 6.f, 9.f, 12.f}) r = m.add(v);'
        ' assert(r == 9.0f); }\n', encoding="utf-8")
    failed = 0
    print("\n== PC のテスト（g++）")
    for src in ("test_features.cpp", "t_filter.cpp"):
        exe = t / src.replace(".cpp", "")
        r = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", src, "-o", exe.name],
                           cwd=t, capture_output=True, text=True)
        if r.returncode == 0:
            r = subprocess.run([str(exe)], cwd=t, capture_output=True, text=True)
        ok = r.returncode == 0
        failed += not ok
        print(f"  {'OK' if ok else '失敗'}: {src}" + ("" if ok else "\n" + (r.stdout + r.stderr)[-1500:]))
    return failed


def main():
    env = devenv.check()
    if not (env["items"]["sdk"] and env["items"]["compiler"]):
        print("Pico SDK かコンパイラがありません:", "・".join(env["problems"]))
        return 2
    boards = sys.argv[1:] or ["pico"]
    where = prepare()
    bad = sum(build(b, where) for b in boards) + pc_tests()
    print("\n" + ("すべて通りました" if bad == 0 else f"問題が {bad} 件あります"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
