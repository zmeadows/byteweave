#!/usr/bin/env python3
"""
Run clang-tidy over all translation units in compile_commands.json.

Usage (CI or local):
  # 1) Configure to produce compile_commands.json (no build required)
  cmake -S . -B build/ci-tidy -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
  # 2) Run tidy
  python3 tools/tidy.py --p build/ci-tidy --warnings-as-errors --jobs 4

Notes:
  - Respects .clang-tidy in the repo.
  - By default runs on all TUs found in compile_commands.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_JOBS = max(os.cpu_count() or 2, 2)

@dataclass
class Args:
    p: Path                         # build dir containing compile_commands.json
    files: list[str]                # optional explicit files to check
    jobs: int
    clang_tidy: str
    extra: list[str]
    warnings_as_errors: bool

def parse_args(argv: list[str]) -> Args:
    ap = argparse.ArgumentParser(description="Run clang-tidy using compile_commands.json")
    ap.add_argument("--p", "--path", dest="p", help="Build dir with compile_commands.json", required=False)
    ap.add_argument("--jobs", "-j", type=int, default=DEFAULT_JOBS, help="Parallelism")
    ap.add_argument("--clang-tidy", default=os.environ.get("CLANG_TIDY", "clang-tidy"), help="clang-tidy binary")
    ap.add_argument("--warnings-as-errors", action="store_true", help="Pass -warnings-as-errors=* to clang-tidy")
    ap.add_argument("files", nargs="*", help="Optional explicit file list (otherwise all from compile_commands.json)")
    # Allow extra args after '--'
    if "--" in argv:
        i = argv.index("--")
        known = argv[:i]
        extra = argv[i+1:]
    else:
        known, extra = argv, []
    ns = ap.parse_args(known)

    # Resolve build dir
    build_dir: Path
    if ns.p:
        build_dir = Path(ns.p).resolve()
    else:
        # Heuristic fallbacks
        for cand in [Path("build/ci-tidy"), Path("build"), Path(".")]:
            if (cand / "compile_commands.json").exists():
                build_dir = cand.resolve()
                break
        else:
            raise SystemExit("compile_commands.json not found; pass --p BUILD_DIR (configure with -DCMAKE_EXPORT_COMPILE_COMMANDS=ON)")

    return Args(
        p=build_dir,
        files=list(ns.files),
        jobs=max(1, ns.jobs),
        clang_tidy=ns.clang_tidy,
        extra=extra,
        warnings_as_errors=bool(ns.warnings_as_errors),
    )

def load_tus(build_dir: Path) -> list[str]:
    compdb = build_dir / "compile_commands.json"
    data = json.loads(compdb.read_text(encoding="utf-8"))
    files: list[str] = []
    seen: set[str] = set()
    for entry in data:
        f = entry.get("file")
        if not isinstance(f, str):
            continue
        # Normalize to repo-relative if possible
        fp = str(Path(f).resolve())
        if fp not in seen:
            seen.add(fp)
            files.append(fp)
    return files

def run_one(clang_tidy: str, build_dir: Path, file: str, extra: list[str], warnings_as_errors: bool) -> int:
    cmd = [clang_tidy, "-quiet", "-p", str(build_dir)]
    if warnings_as_errors:
        cmd.append("-warnings-as-errors=*")
    cmd.append(file)
    if extra:
        cmd.append("--")
        cmd.extend(extra)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(proc.stdout)
    return proc.returncode

def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not (args.p / "compile_commands.json").exists():
        print(f"error: {args.p}/compile_commands.json not found", file=sys.stderr)
        return 2

    files = args.files or load_tus(args.p)
    if not files:
        print("info: no translation units in compile_commands.json", file=sys.stderr)
        return 0

    rc = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_one, args.clang_tidy, args.p, f, args.extra, args.warnings_as_errors): f for f in files}
        for fut in as_completed(futs):
            code = fut.result()
            if code != 0:
                rc = code
    return rc

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
