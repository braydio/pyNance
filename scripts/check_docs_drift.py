#!/usr/bin/env python3
"""Enforce documentation updates for source changes.

This guard complements ``scripts/check_docs.py``. The coverage checker verifies
that touched source files are documented somewhere; this script verifies that a
PR actually changes the relevant documentation when behavior-bearing source
files change.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PREFIXES = ("docs/", "README.md", "CONTRIBUTING.md", "AGENTS.md")
SOURCE_PREFIXES = ("backend/app/", "frontend/src/")
IGNORED_SOURCE_PARTS = {"__tests__", "test", "tests", "__pycache__"}


@dataclass(slots=True)
class DriftFinding:
    """A source file that requires a documentation update."""

    path: Path
    message: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Require documentation updates for changed source files.")
    parser.add_argument(
        "--changed-since",
        metavar="REV",
        required=True,
        help="Git revision to compare against HEAD.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable output.",
    )
    return parser.parse_args(argv)


def git_changed_files(base_rev: str) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", f"{base_rev}..HEAD", "--name-only", "--diff-filter=ACMRT"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def is_doc_path(path: Path) -> bool:
    path_text = path.as_posix()
    return path.suffix.lower() == ".md" and path_text.startswith(DOC_PREFIXES)


def is_source_path(path: Path) -> bool:
    path_text = path.as_posix()
    if not path_text.startswith(SOURCE_PREFIXES):
        return False
    if path.suffix.lower() not in {".py", ".vue", ".js", ".ts"}:
        return False
    return not any(part in IGNORED_SOURCE_PARTS for part in path.parts)


def expected_docs_for_source(path: Path) -> set[Path]:
    """Return documentation files expected to move with a source change."""

    if path.parts[:3] == ("backend", "app", "routes") and path.suffix == ".py":
        return {
            Path("docs/backend/api-reference.md"),
            Path("docs/backend/app/routes") / f"{path.stem}.md",
        }

    if path.parts[:3] == ("backend", "app", "services") and path.suffix == ".py":
        return {Path("docs/backend/app/services") / f"{path.stem}.md"}

    if path.parts[:3] == ("backend", "app", "models") and path.suffix == ".py":
        return {
            Path("docs/backend/app/models.md"),
            Path("docs/backend/DATABASE_OVERVIEW.md"),
        }

    if path.parts[:2] == ("frontend", "src") and path.suffix == ".vue":
        return {
            Path("docs/frontend"),
            Path("docs/ui"),
            Path("docs/devnotes"),
        }

    return {Path("docs")}


def doc_requirement_satisfied(source_path: Path, changed_docs: set[Path]) -> bool:
    expected = expected_docs_for_source(source_path)
    for doc_path in changed_docs:
        for expected_path in expected:
            if doc_path == expected_path:
                return True
            if expected_path.as_posix().endswith("/") and doc_path.as_posix().startswith(expected_path.as_posix()):
                return True
            if expected_path.is_dir() and doc_path.as_posix().startswith(expected_path.as_posix() + "/"):
                return True
            if expected_path.suffix == "" and doc_path.as_posix().startswith(expected_path.as_posix() + "/"):
                return True
    return False


def check_drift(changed_files: Iterable[Path]) -> list[DriftFinding]:
    changed = list(changed_files)
    changed_docs = {path for path in changed if is_doc_path(path)}
    changed_sources = [path for path in changed if is_source_path(path)]

    findings: list[DriftFinding] = []
    for source_path in changed_sources:
        if doc_requirement_satisfied(source_path, changed_docs):
            continue
        expected = ", ".join(sorted(path.as_posix() for path in expected_docs_for_source(source_path)))
        findings.append(
            DriftFinding(
                path=source_path,
                message=f"source changed without matching docs update; expected one of: {expected}",
            )
        )
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        changed_files = git_changed_files(args.changed_since)
    except subprocess.CalledProcessError as exc:
        print(f"[docs-drift] Failed to resolve changed files: {exc}", file=sys.stderr)
        return 2

    findings = check_drift(changed_files)
    if args.json_output:
        print(
            json.dumps(
                {
                    "missing": [
                        {"file": finding.path.as_posix(), "message": finding.message}
                        for finding in findings
                    ]
                },
                indent=2,
            )
        )
    elif findings:
        print("[docs-drift] Documentation updates are required for these source changes:")
        for finding in findings:
            print(f"  - {finding.path.as_posix()}: {finding.message}")
        print("Add the relevant docs update, or comment [no-docs] on the PR to override.")
    else:
        print("[docs-drift] Source changes include matching documentation updates.")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
