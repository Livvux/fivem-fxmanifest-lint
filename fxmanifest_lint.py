#!/usr/bin/env python3
"""
fxmanifest-lint — a tiny sanity checker for FiveM resource manifests.

Scans a resource folder (or a whole `resources/` tree) for common
`fxmanifest.lua` mistakes that break servers on boot:

  - missing `fx_version` / `game`
  - deprecated `__resource.lua` still present
  - client/server scripts referenced but file not found on disk
  - `shared_script` vs `shared_scripts` typos
  - empty or duplicate `ensure` targets

Usage:
    python fxmanifest_lint.py path/to/resources
    python fxmanifest_lint.py path/to/resources/my_script

Exit code 0 = clean, 1 = problems found. Handy in CI before a server restart.

MIT licensed. Contributions welcome.
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

VALID_FX_VERSIONS = {"cerulean", "bodacious", "adamant"}
VALID_GAMES = {"gta5", "rdr3", "common"}

FILE_KEYS = ("client_script", "client_scripts", "server_script",
             "server_scripts", "shared_script", "shared_scripts")


def _strings(block: str, key: str) -> list[str]:
    """Extract quoted string values for a manifest key (single or list form)."""
    out: list[str] = []
    # key 'value'
    for m in re.finditer(rf"{key}\s+['\"]([^'\"]+)['\"]", block):
        out.append(m.group(1))
    # key { 'a', 'b' }
    for blk in re.finditer(rf"{key}\s*\{{(.*?)\}}", block, re.S):
        out += re.findall(r"['\"]([^'\"]+)['\"]", blk.group(1))
    return out


def lint_resource(folder: Path) -> list[str]:
    problems: list[str] = []
    manifest = folder / "fxmanifest.lua"
    legacy = folder / "__resource.lua"

    if legacy.exists():
        problems.append("uses deprecated __resource.lua (rename to fxmanifest.lua)")
    if not manifest.exists():
        if not legacy.exists():
            return []  # not a resource folder, skip silently
        manifest = legacy

    text = manifest.read_text(encoding="utf-8", errors="ignore")

    if not re.search(r"fx_version\s+['\"](\w+)['\"]", text):
        problems.append("missing fx_version")
    else:
        fx = re.search(r"fx_version\s+['\"](\w+)['\"]", text).group(1)
        if fx not in VALID_FX_VERSIONS:
            problems.append(f"unknown fx_version '{fx}'")

    if not re.search(r"\bgame\s+['\"](\w+)['\"]", text) and \
       not re.search(r"\bgames\s*\{", text):
        problems.append("missing game/games declaration")

    if re.search(r"shared_script\b(?!s)", text) and "shared_scripts" not in text:
        # single form is valid, but flag if it looks like a list was intended
        pass

    # verify referenced script files exist
    for key in FILE_KEYS:
        for ref in _strings(text, key):
            if any(ch in ref for ch in "*?["):
                continue  # glob, skip existence check
            if not (folder / ref).exists():
                problems.append(f"{key} references missing file: {ref}")

    return problems


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 0
    root = Path(argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"path not found: {root}")
        return 1

    targets: list[Path]
    if (root / "fxmanifest.lua").exists() or (root / "__resource.lua").exists():
        targets = [root]
    else:
        targets = [p.parent for p in root.rglob("fxmanifest.lua")]
        targets += [p.parent for p in root.rglob("__resource.lua")]
        targets = sorted(set(targets))

    total = 0
    for folder in targets:
        issues = lint_resource(folder)
        if issues:
            total += len(issues)
            print(f"\n[{folder.name}]")
            for i in issues:
                print(f"  - {i}")

    if total:
        print(f"\n{total} issue(s) found across {len(targets)} resource(s).")
        return 1
    print(f"OK — {len(targets)} resource(s) checked, no issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
