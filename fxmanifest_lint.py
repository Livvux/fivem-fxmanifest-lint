#!/usr/bin/env python3
"""Dependency-free fxmanifest.lua tokenizer and validator for FiveM resources."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

RULESET_VERSION = "2.0.0"
RULESET_PATH = Path(__file__).with_name("ruleset-v2.0.0.json")
VALID_FX_VERSIONS = {"cerulean", "bodacious", "adamant"}
VALID_GAMES = {"gta5", "rdr3", "common"}
VALID_NODE_VERSIONS = {"16", "22"}
SINGULAR_PLURAL = {
    "client_script": "client_scripts", "server_script": "server_scripts",
    "shared_script": "shared_scripts", "file": "files",
    "dependency": "dependencies", "game": "games",
}
PLURAL_SINGULAR = {plural: singular for singular, plural in SINGULAR_PLURAL.items()}
FILE_DIRECTIVES = {"client_script", "server_script", "shared_script", "file"}
KNOWN_DIRECTIVES = {
    "fx_version", "game", "games", "client_script", "client_scripts",
    "server_script", "server_scripts", "shared_script", "shared_scripts",
    "file", "files", "dependency", "dependencies", "ui_page", "data_file",
    "lua54", "node_version", "this_is_a_map", "server_only", "loadscreen",
    "loadscreen_manual_shutdown", "provide", "escrow_ignore",
}


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class Directive:
    name: str
    values: list[str]
    line: int
    value_kind: str


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    line: int
    message: str
    docs_url: str


@lru_cache(maxsize=1)
def _rules() -> dict[str, dict[str, str]]:
    with RULESET_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("ruleset_version") != RULESET_VERSION:
        raise RuntimeError("ruleset version does not match the CLI version")
    return {rule["rule_id"]: rule for rule in payload["rules"]}


def _finding(rule_id: str, line: int, message: str | None = None) -> Finding:
    rule = _rules()[rule_id]
    return Finding(rule_id, rule["severity"], max(1, line), message or rule["message"], rule["docs_url"])


def _lex(text: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1
    length = len(text)

    def advance(value: str) -> None:
        nonlocal line, column
        newlines = value.count("\n")
        if newlines:
            line += newlines
            column = len(value.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(value)

    while index < length:
        char = text[index]
        if char in " \t\r":
            advance(char)
            index += 1
            continue
        if char == "\n":
            tokens.append(Token("NEWLINE", "\n", line, column))
            advance(char)
            index += 1
            continue
        if text.startswith("--[[", index):
            end = text.find("]]", index + 4)
            end = length if end < 0 else end + 2
            value = text[index:end]
            advance(value)
            index = end
            continue
        if text.startswith("--", index):
            end = text.find("\n", index + 2)
            end = length if end < 0 else end
            value = text[index:end]
            advance(value)
            index = end
            continue
        if text.startswith("[[", index):
            start_line, start_column = line, column
            end = text.find("]]", index + 2)
            content_end = length if end < 0 else end
            raw_end = length if end < 0 else end + 2
            tokens.append(Token("STRING", text[index + 2:content_end], start_line, start_column))
            value = text[index:raw_end]
            advance(value)
            index = raw_end
            continue
        if char in "'\"":
            quote = char
            start_line, start_column = line, column
            index += 1
            advance(quote)
            value: list[str] = []
            while index < length:
                current = text[index]
                if current == "\\" and index + 1 < length:
                    escaped = text[index + 1]
                    value.append({"n": "\n", "r": "\r", "t": "\t"}.get(escaped, escaped))
                    advance(text[index:index + 2])
                    index += 2
                    continue
                if current == quote:
                    advance(current)
                    index += 1
                    break
                value.append(current)
                advance(current)
                index += 1
            tokens.append(Token("STRING", "".join(value), start_line, start_column))
            continue
        if char.isalpha() or char == "_":
            start = index
            start_line, start_column = line, column
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            value = text[start:index]
            advance(value)
            tokens.append(Token("IDENT", value, start_line, start_column))
            continue
        if char.isdigit() or (char == "-" and index + 1 < length and text[index + 1].isdigit()):
            start = index
            start_line, start_column = line, column
            index += 1
            while index < length and (text[index].isdigit() or text[index] == "."):
                index += 1
            value = text[start:index]
            advance(value)
            tokens.append(Token("BARE", value, start_line, start_column))
            continue
        tokens.append(Token(char, char, line, column))
        advance(char)
        index += 1
    return tokens


def _consume_group(tokens: Sequence[Token], index: int, opening: str, closing: str) -> tuple[list[str], int, bool]:
    values: list[str] = []
    depth = 0
    saw_table = opening == "{"
    while index < len(tokens):
        token = tokens[index]
        if token.kind == opening:
            depth += 1
        elif token.kind == closing:
            depth -= 1
            if depth == 0:
                return values, index + 1, saw_table
        elif token.kind == "{" and opening == "(":
            table_values, next_index, _ = _consume_group(tokens, index, "{", "}")
            values.extend(table_values)
            saw_table = True
            index = next_index
            continue
        elif token.kind in {"STRING", "BARE"}:
            values.append(token.value)
        index += 1
    return values, index, saw_table


def tokenize_manifest(text: str) -> list[Directive]:
    """Tokenize top-level manifest declarations without executing Lua."""
    tokens = _lex(text)
    directives: list[Directive] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind != "IDENT":
            index += 1
            continue
        name = token.value
        index += 1
        while index < len(tokens) and tokens[index].kind == "NEWLINE":
            index += 1
        values: list[str] = []
        value_kind = "invalid"
        if index < len(tokens) and tokens[index].kind == "(":
            values, index, saw_table = _consume_group(tokens, index, "(", ")")
            value_kind = "table" if saw_table else "scalar"
            while index < len(tokens) and tokens[index].kind == "(":
                extra, index, extra_table = _consume_group(tokens, index, "(", ")")
                values.extend(extra)
                value_kind = "table" if extra_table else value_kind
        elif index < len(tokens) and tokens[index].kind == "{":
            values, index, _ = _consume_group(tokens, index, "{", "}")
            value_kind = "table"
        elif index < len(tokens) and tokens[index].kind in {"STRING", "BARE"}:
            first = tokens[index]
            values.append(first.value)
            value_kind = "scalar"
            index += 1
            if name == "data_file":
                while index < len(tokens) and tokens[index].kind == "," and tokens[index].line == first.line:
                    index += 1
                if index < len(tokens) and tokens[index].kind in {"STRING", "BARE"} and tokens[index].line == first.line:
                    values.append(tokens[index].value)
                    index += 1
        if name in KNOWN_DIRECTIVES or values:
            directives.append(Directive(name, values, token.line, value_kind))
    return directives


def _group(directives: Iterable[Directive]) -> dict[str, list[Directive]]:
    grouped: dict[str, list[Directive]] = {}
    for directive in directives:
        grouped.setdefault(directive.name, []).append(directive)
    return grouped


def _covers_file(reference: str, declared_files: Iterable[str]) -> bool:
    return any(reference == pattern or fnmatch.fnmatch(reference, pattern) for pattern in declared_files)


def _path_matches(resource_dir: Path, reference: str) -> bool:
    path_reference = Path(reference)
    if path_reference.is_absolute() or ".." in path_reference.parts:
        return False
    if any(character in reference for character in "*?["):
        try:
            return any(resource_dir.glob(reference))
        except (NotImplementedError, OSError, ValueError):
            return False
    try:
        candidate = (resource_dir / reference).resolve()
        candidate.relative_to(resource_dir.resolve())
    except (OSError, ValueError):
        return False
    return candidate.is_file()


def validate_text(text: str, resource_dir: Path | None = None, max_bytes: int | None = None) -> list[Finding]:
    if max_bytes is not None and len(text.encode("utf-8")) > max_bytes:
        return [_finding("FXM017", 1)]
    directives = tokenize_manifest(text)
    grouped = _group(directives)
    findings: list[Finding] = []

    versions = grouped.get("fx_version", [])
    if not versions:
        findings.append(_finding("FXM001", 1))
    elif not versions[0].values or versions[0].values[0] not in VALID_FX_VERSIONS:
        value = versions[0].values[0] if versions[0].values else ""
        findings.append(_finding("FXM002", versions[0].line, f"Invalid fx_version '{value}'. Use cerulean, bodacious, or adamant."))
    games = grouped.get("game", []) + grouped.get("games", [])
    if not games:
        findings.append(_finding("FXM003", 1))
    else:
        for directive in sorted(games, key=lambda item: item.line):
            invalid = [value for value in directive.values if value not in VALID_GAMES]
            if not directive.values or invalid:
                value = invalid[0] if invalid else ""
                findings.append(_finding("FXM004", directive.line, f"Invalid game '{value}'. Use gta5, rdr3, or common."))
                break
    for directive in grouped.get("lua54", []):
        findings.append(_finding("FXM005", directive.line))
    for directive in grouped.get("node_version", []):
        value = directive.values[0] if directive.values else ""
        if value not in VALID_NODE_VERSIONS:
            findings.append(_finding("FXM006", directive.line, f"Invalid node_version '{value}'. Use 16 or 22."))
    for entries in [versions, games, grouped.get("ui_page", []), grouped.get("node_version", [])]:
        if len(entries) > 1:
            findings.append(_finding("FXM007", sorted(entries, key=lambda item: item.line)[1].line))
    for directive in directives:
        if directive.name in PLURAL_SINGULAR and directive.value_kind != "table":
            findings.append(_finding("FXM012", directive.line, f"Plural directive '{directive.name}' requires a table."))
        elif directive.name in SINGULAR_PLURAL and directive.value_kind != "scalar":
            findings.append(_finding("FXM012", directive.line, f"Singular directive '{directive.name}' requires one scalar value."))

    normalized: dict[str, dict[str, int]] = {}
    for directive in directives:
        canonical = PLURAL_SINGULAR.get(directive.name, directive.name)
        if canonical not in FILE_DIRECTIVES | {"dependency"}:
            continue
        seen = normalized.setdefault(canonical, {})
        for value in directive.values:
            if value in seen:
                findings.append(_finding("FXM013", directive.line, f"Duplicate {canonical} entry '{value}'."))
            else:
                seen[value] = directive.line
    declared_files = normalized.get("file", {})
    for directive in grouped.get("ui_page", []):
        if directive.values and "://" not in directive.values[0] and not _covers_file(directive.values[0], declared_files):
            findings.append(_finding("FXM008", directive.line, f"ui_page '{directive.values[0]}' is not covered by file/files."))
    for directive in grouped.get("data_file", []):
        if len(directive.values) != 2:
            findings.append(_finding("FXM015", directive.line))
        elif not _covers_file(directive.values[1], declared_files):
            findings.append(_finding("FXM014", directive.line, f"data_file path '{directive.values[1]}' is not covered by file/files."))

    if resource_dir is not None:
        resource_dir = Path(resource_dir).resolve()
        for directive in directives:
            canonical = PLURAL_SINGULAR.get(directive.name, directive.name)
            if canonical not in FILE_DIRECTIVES:
                continue
            for reference in directive.values:
                if reference.startswith("@"):
                    external = reference[1:].split("/", 1)
                    if len(external) != 2 or not external[0] or not external[1]:
                        findings.append(_finding("FXM009", directive.line, f"Invalid external resource reference '{reference}'."))
                        continue
                    external_root = resource_dir.parent / external[0]
                    if not external_root.is_dir():
                        findings.append(_finding("FXM011", directive.line, f"External resource '{external[0]}' was not found next to this resource."))
                    elif not _path_matches(external_root, external[1]):
                        findings.append(_finding("FXM009", directive.line, f"External reference '{reference}' matched no local file."))
                    continue
                if not _path_matches(resource_dir, reference):
                    rule_id = "FXM010" if any(character in reference for character in "*?[") else "FXM009"
                    findings.append(_finding(rule_id, directive.line, f"{directive.name} reference '{reference}' matched no local file."))
        for directive in grouped.get("dependency", []) + grouped.get("dependencies", []):
            for dependency in directive.values:
                if not dependency.startswith("/") and not (resource_dir.parent / dependency).is_dir():
                    findings.append(_finding("FXM011", directive.line, f"Dependency '{dependency}' was not found next to this resource."))
    return findings


def _targets(root: Path) -> list[Path]:
    if root.is_file():
        return [root.parent] if root.name in {"fxmanifest.lua", "__resource.lua"} else []
    if (root / "fxmanifest.lua").is_file() or (root / "__resource.lua").is_file():
        return [root]
    return sorted({path.parent for name in ("fxmanifest.lua", "__resource.lua") for path in root.rglob(name)})


def _validate_resource(folder: Path) -> list[Finding]:
    manifest = folder / "fxmanifest.lua"
    legacy = folder / "__resource.lua"
    findings = [_finding("FXM018", 1)] if legacy.is_file() else []
    source = manifest if manifest.is_file() else legacy
    if source.is_file():
        findings.extend(validate_text(source.read_text(encoding="utf-8", errors="replace"), resource_dir=folder))
    return findings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate FiveM fxmanifest.lua files without executing them.")
    parser.add_argument("path", nargs="?", help="resource directory, manifest file, or resources tree")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument("--version", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.version:
        print(f"fivem-fxmanifest-lint {RULESET_VERSION}")
        return 0
    if not arguments.path:
        _parser().print_usage(sys.stderr)
        return 2
    try:
        root = Path(arguments.path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"path not found: {root}")
        targets = _targets(root)
        if not targets:
            raise FileNotFoundError(f"no fxmanifest.lua or __resource.lua found under: {root}")
        results = [(target, _validate_resource(target)) for target in targets]
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    all_findings = [(resource, finding) for resource, findings in results for finding in findings]
    if arguments.output_format == "json":
        payload = []
        for resource, finding in all_findings:
            item = asdict(finding)
            item["resource"] = str(resource)
            payload.append(item)
        print(json.dumps({"tool": "fivem-fxmanifest-lint", "ruleset_version": RULESET_VERSION, "resources_checked": len(results), "findings": payload}, indent=2, sort_keys=True))
    else:
        for resource, findings in results:
            if findings:
                print(f"\n[{resource.name}]")
                for finding in findings:
                    print(f"  {finding.severity.upper():7} {finding.rule_id} line {finding.line}: {finding.message}")
        if all_findings:
            print(f"\n{len(all_findings)} finding(s) across {len(results)} resource(s). Ruleset {RULESET_VERSION}.")
        else:
            print(f"OK — {len(results)} resource(s) checked with ruleset {RULESET_VERSION}.")
    has_errors = any(finding.severity == "error" for _, finding in all_findings)
    has_warnings = any(finding.severity == "warning" for _, finding in all_findings)
    return 1 if has_errors or (arguments.fail_on_warnings and has_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
