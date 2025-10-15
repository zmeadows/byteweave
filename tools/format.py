#!/usr/bin/env python3
"""
Format C++ sources with clang-format.

- Formats:   **/*.cpp, **/*.hpp, **/*.inl  (editable below)
- Skips:     **/*.hpp.in and common build/output dirs (editable below)
- Honors:    repo .clang-format via -style=file
- Options:   --check (non-zero exit if any file would be reformatted)
             --jobs N (parallelism)
             --clang-format /path/to/clang-format
             --root /path/to/repo (defaults to repo root inferred from this file)

Usage:
  python3 tools/format.py
  python3 tools/format.py --check
  CLANG_FORMAT=clang-format-18 python3 tools/format.py --jobs 8
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

# ------------------------ EDITABLE CONFIG -------------------------------------
FILE_GLOBS: list[str] = ["**/*.cpp", "**/*.hpp", "**/*.inl"]
EXCLUDE_GLOBS: list[str] = ["**/*.hpp.in"]
EXCLUDE_DIRS: list[str] = [".git", "build", "dist", "out", "cmake-build*"]
# -----------------------------------------------------------------------------


def infer_repo_root(default: Path) -> Path:
    """Prefer git root; fallback to provided default."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        )
        return Path(out.strip())
    except Exception:
        return default


def is_under_excluded_dir(p: Path, root: Path) -> bool:
    """Return True if any path component matches EXCLUDE_DIRS patterns."""
    rel = p.relative_to(root)
    for part in rel.parts[:-1]:  # exclude the filename itself
        for pat in EXCLUDE_DIRS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False


def collect_files(root: Path) -> list[Path]:
    """Collect files matching FILE_GLOBS, minus EXCLUDE_GLOBS and EXCLUDE_DIRS."""
    files: set[Path] = set()
    for pattern in FILE_GLOBS:
        for p in root.glob(pattern):
            if not p.is_file():
                continue
            if is_under_excluded_dir(p, root):
                continue
            # Per-file excludes
            skip = any(
                fnmatch.fnmatch(str(p.relative_to(root)), pat) for pat in EXCLUDE_GLOBS
            )
            if skip:
                continue
            files.add(p)
    return sorted(files)


def run_clang_format(
    clang_format: str, file: Path, check: bool
) -> tuple[Path, int, str, str]:
    """
    Run clang-format on a single file.
    Returns (file, returncode, stdout, stderr).
    """
    args = [clang_format, "-style=file"]
    if check:
        # Dry-run; non-zero if reformatting would occur (or on error)
        args += ["-n", "--Werror"]
    else:
        # In-place edit
        args += ["-i"]

    args.append(str(file))
    proc = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return file, proc.returncode, proc.stdout, proc.stderr


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Format C++ sources with clang-format.")
    ap.add_argument(
        "--check", "-c", action="store_true", help="Dry run; fail if reformat needed."
    )
    ap.add_argument(
        "--jobs", "-j", type=int, default=os.cpu_count() or 4, help="Parallel jobs."
    )
    ap.add_argument(
        "--clang-format",
        default=os.environ.get("CLANG_FORMAT", "clang-format"),
        help="clang-format binary to use (default: env CLANG_FORMAT or 'clang-format').",
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: git root or repo parent of this script).",
    )
    args = ap.parse_args(argv)

    # Resolve root (script is expected at <root>/tools/format.py)
    default_root = Path(__file__).resolve().parents[1]
    root = infer_repo_root(default_root) if args.root is None else args.root.resolve()

    # Sanity: check clang-format exists
    if not shutil_which(args.clang_format):
        print(f"error: '{args.clang_format}' not found in PATH", file=sys.stderr)
        return 127

    files = collect_files(root)
    if not files:
        print("No files to format.")
        return 0

    check = bool(args.check)
    would_change: list[Path] = []
    failures: list[tuple[Path, str]] = []

    with futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(run_clang_format, args.clang_format, f, check) for f in files]
        for fut in futures.as_completed(futs):
            file, code, out, err = fut.result()
            if code == 0:
                continue
            # clang-format returns non-zero if reformat would occur (with -n --Werror) OR on error.
            # Heuristics: if stderr empty, we assume "would change", else surface error.
            if check and not err.strip():
                would_change.append(file)
            else:
                failures.append((file, (err or out).strip()))

    if check:
        if failures:
            print("clang-format errors:\n", file=sys.stderr)
            for f, msg in failures:
                print(
                    f"  {f}:\n    {msg.replace(os.linesep, os.linesep + '    ')}",
                    file=sys.stderr,
                )
            return 2
        if would_change:
            print("Files that would be reformatted:")
            for f in would_change:
                print(f"  {f}")
            return 1
        print("All files are properly formatted.")
        return 0

    # Format mode summary
    if failures:
        print("Some files failed to format:", file=sys.stderr)
        for f, msg in failures:
            print(
                f"  {f}:\n    {msg.replace(os.linesep, os.linesep + '    ')}",
                file=sys.stderr,
            )
        return 2

    print(f"Formatted {len(files)} file(s).")
    return 0


def shutil_which(cmd: str) -> str | None:
    """Minimal reimplementation of shutil.which to avoid an extra import if desired."""
    import shutil

    return shutil.which(cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
