from __future__ import annotations

import argparse
import fnmatch
import glob
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .scanner import Finding, scan_file

if TYPE_CHECKING:
    from collections.abc import Sequence

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


@dataclass
class ScanResult:
    findings: list[Finding]
    files_scanned: int
    had_error: bool


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assert-one-assert-per-pytest",
        description="Assert that each pytest test function contains exactly one assert statement.",
    )

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=(
            "One or more file paths, directory paths, or glob patterns to scan. "
            "Directories are scanned recursively for Python files."
        ),
    )

    parser.add_argument(
        "--exclude",
        metavar="PATTERNS",
        help="Comma-separated glob patterns to exclude files.",
    )

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output. Exit code indicates success (0) or findings (1).",
    )
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Output only the count of findings.",
    )
    output_group.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing information.",
    )

    behavior_group = parser.add_mutually_exclusive_group()
    behavior_group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit immediately after finding the first issue.",
    )
    behavior_group.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit with code 0, even if findings exist.",
    )

    return parser


def parse_patterns(patterns_str: str | None) -> list[str]:
    if not patterns_str:
        return []
    return [p.strip() for p in patterns_str.split(",") if p.strip()]


def _is_glob_pattern(path: str) -> bool:
    return any(c in path for c in ("*", "?", "["))


def _expand_glob(pattern: str) -> tuple[list[str], bool]:
    matched = glob.glob(pattern, recursive=True, include_hidden=True)
    files = []
    for path in matched:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(_expand_directory(path))
    return (files, bool(matched))


def _expand_directory(directory: str) -> list[str]:
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in filenames:
            if filename.endswith(".py"):
                files.append(os.path.join(root, filename))
    return files


def _iter_files(paths: Sequence[str]) -> tuple[list[str], list[str]]:
    files: list[str] = []
    missing: list[str] = []

    for path in paths:
        if _is_glob_pattern(path):
            matched_files, found = _expand_glob(path)
            if found:
                files.extend(matched_files)
            else:
                missing.append(path)
        elif os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(_expand_directory(path))
        else:
            missing.append(path)

    seen: set[str] = set()
    unique_files: list[str] = []
    for f in files:
        normalized = os.path.normpath(f)
        if normalized not in seen:
            seen.add(normalized)
            unique_files.append(f)

    return (unique_files, missing)


def _should_skip_file(path: str, exclude_patterns: list[str]) -> bool:
    if not exclude_patterns:
        return False

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def process_files(
    files: list[str],
    exclude_patterns: list[str],
    verbose: bool = False,
    fail_fast: bool = False,
) -> ScanResult:
    findings: list[Finding] = []
    files_scanned = 0
    had_error = False

    for path in sorted(files):
        if not path.endswith(".py"):
            continue

        if _should_skip_file(path, exclude_patterns):
            if verbose:
                print(f"Skipping (excluded): {path}")
            continue

        if verbose:
            print(f"Scanning: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
            had_error = True
            continue

        try:
            file_findings = scan_file(path, content)
        except SyntaxError as e:
            print(f"Syntax error in {path}: {e}", file=sys.stderr)
            had_error = True
            continue

        files_scanned += 1
        findings.extend(file_findings)

        if file_findings and verbose:
            for finding in file_findings:
                print(f"  Found: {finding}")

        if findings and fail_fast:
            break

    return ScanResult(
        findings=findings,
        files_scanned=files_scanned,
        had_error=had_error,
    )


def output_findings(
    findings: list[Finding],
    count_mode: bool = False,
) -> None:
    if count_mode:
        print(len(findings))
    else:
        for finding in findings:
            print(finding)


def determine_exit_code(result: ScanResult, warn_only: bool = False) -> int:
    if warn_only:
        return EXIT_SUCCESS
    if result.findings:
        return EXIT_FINDINGS
    if result.had_error:
        return EXIT_ERROR
    return EXIT_SUCCESS


def main(argv: Sequence[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    exclude_patterns = parse_patterns(args.exclude)

    files, missing = _iter_files(args.files)

    for path in missing:
        print(f"Error: Path not found: {path}", file=sys.stderr)

    if not files and missing:
        sys.exit(EXIT_ERROR)

    if args.verbose:
        print(f"Scanning {len(files)} file(s) for pytest tests...")
        if exclude_patterns:
            print(f"Excluding patterns: {', '.join(exclude_patterns)}")
        print()

    result = process_files(
        files=files,
        exclude_patterns=exclude_patterns,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
    )

    if missing:
        result.had_error = True

    if args.verbose:
        print()
        print(f"Files scanned: {result.files_scanned}")
        print(f"Findings: {len(result.findings)}")
        if result.had_error:
            print("Errors occurred during scanning.")
    elif not args.quiet:
        output_findings(result.findings, args.count)

    sys.exit(determine_exit_code(result, args.warn_only))
