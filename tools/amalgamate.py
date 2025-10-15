#!/usr/bin/env python3
"""
amalgamate.py — flatten byteweave headers into a single-header distribution.

Usage:
  python3 tools/amalgamate.py --entry include/byteweave/byteweave.hpp \
                              --out dist/byteweave-X.Y.Z.single.hpp   \
                              --version X.Y.Z                         \
                              [--generated build/generated]

Rules:
- Inlines any #include of headers under the "byteweave/" include subtree (including .inl).
- Leaves system headers (#include <vector>, etc.) untouched.
- Strips #pragma once lines from inlined headers.
- Prepends a small preamble that sets BYTEWEAVE_AMALGAMATED=1 (config.hpp aliases BYTEWEAVE_HEADER_ONLY to it) and provides export shims.
- Inlines byteweave/config.hpp directly (authoritative defaults).
- Inlines the configured byteweave/version.hpp from --generated if present; otherwise
  bakes version macros from --version as a fallback.
- Skips byteweave/export.hpp (we provide BW_API shim in preamble).
"""
import argparse
import datetime
import pathlib
import re
import sys
from typing import Optional

RE_INCLUDE = re.compile(r'^\s*#\s*include\s*([<"])([^">]+)[>"]')
RE_SEMVER = re.compile(r"^\s*(\d+)\.(\d+)\.(\d+)(?:[-+].*)?\s*$")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--entry", required=True, help="Path to the umbrella header (byteweave.hpp)"
    )
    ap.add_argument("--out", required=True, help="Output single header path")
    ap.add_argument(
        "--version", required=True, help="Version string to bake in (e.g., 0.1.0)"
    )
    ap.add_argument(
        "--generated",
        default=None,
        help="Path to directory containing configured headers (e.g., build/generated)",
    )
    return ap.parse_args()


def is_local_byteweave(path: str) -> bool:
    return path.startswith("byteweave/")


def resolve_local(
    path: str, repo_root: pathlib.Path, gen_dir: Optional[pathlib.Path]
) -> pathlib.Path:
    # Prefer configured version header if requested and available
    if path == "byteweave/version.hpp" and gen_dir is not None:
        cand = gen_dir / "byteweave" / "version.hpp"
        if cand.exists():
            return cand
    # Otherwise fall back to source include tree
    return repo_root / "include" / path


def inline_file(
    p: pathlib.Path,
    repo_root: pathlib.Path,
    gen_dir: Optional[pathlib.Path],
    seen: set[str],
) -> str:
    text = p.read_text(encoding="utf-8")
    # In single-header mode we set BYTEWEAVE_AMALGAMATED=1 in the preamble.
    # config.hpp defines BYTEWEAVE_HEADER_ONLY to BYTEWEAVE_AMALGAMATED if not already defined; this keeps a single textual definition.
    out_lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#pragma once"):
            continue
        m = RE_INCLUDE.match(line)
        if m:
            inc = m.group(2)
            if is_local_byteweave(inc):
                # Skip export.hpp entirely (we provide BW_API shim in preamble)
                base = inc.split("/")[-1]
                if base in ("export.hpp",):
                    continue

                # If no configured headers dir, skip version.hpp (preamble provides version macros)
                if inc == "byteweave/version.hpp" and gen_dir is None:
                    continue

                full = resolve_local(inc, repo_root, gen_dir)
                key = str(full.resolve())
                if key in seen:
                    continue
                seen.add(key)
                out_lines.append(f"\n// ---- Begin inlined: <{inc}> ----\n")
                out_lines.append(inline_file(full, repo_root, gen_dir, seen))
                out_lines.append(f"\n// ---- End inlined: <{inc}> ----\n")
                continue
        out_lines.append(line)
    return "\n".join(out_lines)


def main() -> None:
    args = parse_args()
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    entry = pathlib.Path(args.entry)
    if not entry.exists():
        print(f"Entry header not found: {entry}", file=sys.stderr)
        sys.exit(2)

    gen_dir = pathlib.Path(args.generated).resolve() if args.generated else None

    # Determine whether to emit version macros in the preamble (fallback)
    use_preamble_version = True
    if gen_dir is not None and (gen_dir / "byteweave" / "version.hpp").exists():
        use_preamble_version = False

    # Parse numerics from --version for the fallback case
    maj, minor, patch = "0", "0", "0"
    m = RE_SEMVER.match(args.version)
    if m:
        maj, minor, patch = m.groups()
    else:
        if use_preamble_version:
            print(
                f"[amalgamate] WARN: '--version {args.version}' is not SemVer (X.Y.Z); using 0.0.0 numerics",
                file=sys.stderr,
            )

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    preamble = f"""// byteweave single-header (amalgamated)
// Generated by tools/amalgamate.py on {ts}
// Version: {args.version}
// DO NOT EDIT THIS FILE MANUALLY.

#pragma once

#ifndef BYTEWEAVE_AMALGAMATED
#  define BYTEWEAVE_AMALGAMATED 1
#endif
"""
    if use_preamble_version:
        preamble += f"""
// Version macros (baked-in fallback)
#ifndef BYTEWEAVE_VERSION_MAJOR
#  define BYTEWEAVE_VERSION_MAJOR {maj}
#endif
#ifndef BYTEWEAVE_VERSION_MINOR
#  define BYTEWEAVE_VERSION_MINOR {minor}
#endif
#ifndef BYTEWEAVE_VERSION_PATCH
#  define BYTEWEAVE_VERSION_PATCH {patch}
#endif
#ifndef BYTEWEAVE_VERSION_STRING
#  define BYTEWEAVE_VERSION_STRING "{args.version}"
#endif
"""

    preamble += """
// Export shims in single-header mode
#ifndef BW_API
#  define BW_API
#endif
"""

    # TODO[@zmeadows][P1]: check for errors here
    body = inline_file(entry, repo_root, gen_dir, seen=set())
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(preamble + "\n" + body + "\n", encoding="utf-8")
    print(f"Wrote single header to {out_path}")


if __name__ == "__main__":
    main()
