#!/usr/bin/env python3
"""Validate documentation front matter for ownership and freshness.

This linter scans Markdown files for a leading front matter block with the
fields ``Owner``, ``Last Updated``, and ``Status``. It fails when any of these
fields are missing, empty, or when the ``Last Updated`` value exceeds the
allowed age threshold. The script is intentionally lightweight so it can run in
CI without additional dependencies.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

DEFAULT_TARGETS = [
    Path("docs/backend/app/routes"),
    Path("docs/backend/app/__init__.md"),
    Path("docs/backend/app/extensions.md"),
    Path("docs/backend/app/models.md"),
]
REQUIRED_KEYS = ("Owner", "Last Updated", "Status")


@dataclass(slots=True)
class LintResult:
    """Outcome of validating a single documentation file."""

    path: Path
    passed: bool
    message: str | None = None


def parse_front_matter(text: str) -> dict[str, str] | None:
    """Extract front matter key/value pairs from the provided text.

    Args:
        text: Full contents of a Markdown document.

    Returns:
        Mapping of front matter keys to values when a block exists; otherwise
        ``None``.
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    content: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        content[key.strip()] = value.strip()
    return content if content else None


def is_stale(last_updated: str, max_age_days: int) -> bool:
    """Determine whether a ``Last Updated`` value exceeds the age threshold."""

    parsed_date = datetime.strptime(last_updated, "%Y-%m-%d").date()
    return (date.today() - parsed_date).days > max_age_days


def collect_markdown_files(paths: Iterable[Path]) -> list[Path]:
    """Resolve Markdown files from the provided paths."""

    collected: list[Path] = []
    for path in paths:
        if path.is_dir():
            collected.extend(sorted(path.rglob("*.md")))
        elif path.suffix.lower() == ".md" and path.exists():
            collected.append(path)
    return collected


def lint_file(path: Path, max_age_days: int) -> LintResult:
    """Validate a single Markdown document."""

    text = path.read_text(encoding="utf-8")
    front_matter = parse_front_matter(text)
    if front_matter is None:
        return LintResult(
            path=path, passed=False, message="missing front matter header"
        )

    missing = [key for key in REQUIRED_KEYS if not front_matter.get(key)]
    if missing:
        missing_keys = ", ".join(missing)
        return LintResult(
            path=path, passed=False, message=f"missing keys: {missing_keys}"
        )

    last_updated = front_matter.get("Last Updated")
    if last_updated is None:
        return LintResult(path=path, passed=False, message="missing Last Updated")

    try:
        if is_stale(last_updated, max_age_days):
            return LintResult(
                path=path,
                passed=False,
                message=(
                    f"Last Updated {last_updated} is older than {max_age_days} days; "
                    "refresh or confirm accuracy"
                ),
            )
    except ValueError:
        return LintResult(
            path=path,
            passed=False,
            message="invalid Last Updated format; use YYYY-MM-DD",
        )

    return LintResult(path=path, passed=True)


def run_lint(paths: Iterable[Path], max_age_days: int) -> list[LintResult]:
    """Execute lint checks across the provided paths."""

    markdown_files = collect_markdown_files(paths)
    return [lint_file(path, max_age_days) for path in markdown_files]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Configure CLI arguments for the front matter linter."""

    parser = argparse.ArgumentParser(
        description="Validate documentation front matter blocks."
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        type=Path,
        default=DEFAULT_TARGETS,
        help="Files or directories to scan (defaults to key backend docs).",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=180,
        help="Fail when Last Updated exceeds this many days (default: 180).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for command-line execution."""

    args = parse_args(argv)
    results = run_lint(args.paths, args.max_age_days)

    failures = [result for result in results if not result.passed]
    if failures:
        print("Front matter lint failures:")
        for failure in failures:
            print(f"  - {failure.path}: {failure.message}")
        return 1

    if results:
        print(
            f"Validated {len(results)} documentation files; no front matter issues found."
        )
    else:
        print("No documentation files found to lint.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
