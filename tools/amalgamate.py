#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


class AmalgamationError(Exception):
    """Fatal amalgamation error for invalid input or missing files."""


@dataclass
class Args:
    entry: Path
    out: Path
    version: str
    generated: Path | None
    repo_root: Path


def parse_args(argv: list[str]) -> Args:
    p = argparse.ArgumentParser(
        description="Amalgamate Byteweave headers into a single header."
    )
    p.add_argument(
        "--entry",
        required=True,
        help="Umbrella header: include/byteweave/byteweave.hpp",
    )
    p.add_argument(
        "--out",
        required=True,
        help="Output single-header path (e.g., dist/byteweave-X.Y.Z.single.hpp)",
    )
    p.add_argument(
        "--version",
        required=True,
        help="Version X.Y.Z (used when --generated is not provided)",
    )
    p.add_argument(
        "--generated",
        help="Build include dir containing generated/byteweave/version.hpp",
    )
    ns = p.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    def abs_or_repo(pth: str) -> Path:
        p = Path(pth)
        return (repo_root / p).resolve() if not p.is_absolute() else p.resolve()

    entry = abs_or_repo(ns.entry)
    out = abs_or_repo(ns.out)
    generated: Path | None = abs_or_repo(ns.generated) if ns.generated else None

    return Args(
        entry=entry,
        out=out,
        version=ns.version,
        generated=generated,
        repo_root=repo_root,
    )


LOCAL_PREFIX = "byteweave/"
EXPORT_HEADER = f"{LOCAL_PREFIX}export.hpp"
VERSION_HEADER = f"{LOCAL_PREFIX}version.hpp"

_include_rx = re.compile(r'^\s*#\s*include\s*([<"])([^">]+)[>"]')


def parse_include(line: str) -> tuple[str, str] | None:
    m = _include_rx.match(line)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def is_local_byteweave(path: str) -> bool:
    return path.startswith(LOCAL_PREFIX)


def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def version_triplet(version: str) -> tuple[int, int, int]:
    m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)\s*$", version)
    if not m:
        raise AmalgamationError(f"Invalid --version '{version}'. Expected X.Y.Z")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def resolve_local(
    path_fragment: str, repo_root: Path, generated: Path | None
) -> Path | None:
    if path_fragment == EXPORT_HEADER:
        return None
    if path_fragment == VERSION_HEADER:
        if generated is not None:
            cand = (generated / path_fragment).resolve()
            if not cand.exists():
                raise AmalgamationError(
                    f"Expected generated version header missing: {cand}"
                )
            return cand
        return Path("__SYNTHESIZE_VERSION__")
    cand = (repo_root / "include" / path_fragment).resolve()
    if cand.exists():
        return cand
    raise AmalgamationError(f"Unable to resolve local include '{path_fragment}'")


def inline_file(
    path: Path, repo_root: Path, generated: Path | None, seen: set[Path]
) -> str:
    if path in seen:
        return ""
    if str(path) == "__SYNTHESIZE_VERSION__":
        return ""
    if not path.exists():
        raise AmalgamationError(f"Missing input file: {path}")
    seen.add(path)
    text = normalize_newlines(path.read_text(encoding="utf-8"))
    out_lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#pragma once"):
            continue
        parsed = parse_include(line)
        if not parsed:
            out_lines.append(line)
            continue
        _, inc = parsed
        # Inline any include under byteweave/ (regardless of <> or "")
        if not is_local_byteweave(inc):
            out_lines.append(line)
            continue
        if inc == EXPORT_HEADER:
            continue
        target = resolve_local(inc, repo_root, generated)
        if target is None:
            continue
        if str(target) == "__SYNTHESIZE_VERSION__":
            continue
        out_lines.append(f"// begin: {inc}")
        out_lines.append(inline_file(target, repo_root, generated, seen))
        out_lines.append(f"// end: {inc}")
    return "\n".join(out_lines)


def version_text(version: str) -> str:
    major, minor, patch = version_triplet(version)
    # No '#pragma once' here to keep exactly one pragma in output (preamble only)
    return f"""#define BYTEWEAVE_VERSION_MAJOR {major}
#define BYTEWEAVE_VERSION_MINOR {minor}
#define BYTEWEAVE_VERSION_PATCH {patch}
#define BYTEWEAVE_VERSION_STRING "{major}.{minor}.{patch}"
"""


def build_preamble() -> str:
    # Do NOT define BYTEWEAVE_HEADER_ONLY here; config.hpp provides the alias.
    return """#pragma once
#ifndef BYTEWEAVE_AMALGAMATED
#  define BYTEWEAVE_AMALGAMATED 1
#endif

#ifndef BW_API
#  define BW_API
#endif
"""


def main() -> None:
    args = parse_args(sys.argv[1:])
    if not args.entry.exists():
        raise AmalgamationError(f"--entry not found: {args.entry}")
    if args.generated is not None and not args.generated.exists():
        raise AmalgamationError(f"--generated directory not found: {args.generated}")
    seen: set[Path] = set()
    body = inline_file(args.entry, args.repo_root, args.generated, seen)
    needs_version = True
    if args.generated is not None:
        gen_version = (args.generated / VERSION_HEADER).resolve()
        if gen_version.exists():
            needs_version = False
    if "BYTEWEAVE_VERSION_MAJOR" in body:
        needs_version = False
    preamble = build_preamble()
    pieces: list[str] = [preamble]
    if needs_version:
        pieces.append("// synthesized: byteweave/version.hpp")
        pieces.append(version_text(args.version))
    pieces.append(body)
    out_text = "\n".join(pieces).rstrip() + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_text, encoding="utf-8")
    print(f"Wrote single header to {args.out}")


if __name__ == "__main__":
    try:
        main()
    except AmalgamationError as e:
        print(f"[amalgamate] error: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("[amalgamate] interrupted", file=sys.stderr)
        sys.exit(130)
