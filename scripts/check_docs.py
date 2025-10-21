#!/usr/bin/env python3
"""Verify documentation coverage for backend Python and frontend Vue files.

This script inspects staged or specified files and ensures that each touched
backend Python or frontend Vue file is mentioned somewhere in the corresponding
`docs/backend` or `docs/frontend` trees. The check is intentionally forgiving:
it looks for several common reference patterns (file path, file name, module
name, or component name) so that teams can document modules either in dedicated
Markdown files or in consolidated feature guides.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOTS = {
    "backend": REPO_ROOT / "docs" / "backend",
    "frontend": REPO_ROOT / "docs" / "frontend",
}
SUPPORTED_SUFFIXES = {".py", ".vue"}


@dataclass(slots=True)
class FileDocResult:
    """Documentation lookup result for a single source file."""

    file_path: Path
    category: str
    doc_path: Path | None
    message: str | None = None

    @property
    def is_documented(self) -> bool:
        """Return ``True`` when a documentation path has been resolved."""

        return self.doc_path is not None


class DocCorpus:
    """In-memory index of documentation files for a given category."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._documents: list[tuple[Path, str]] | None = None

    @property
    def documents(self) -> list[tuple[Path, str]]:
        """Return cached documentation contents, loading them on first access."""

        if self._documents is None:
            docs: list[tuple[Path, str]] = []
            if not self.root.exists():
                self._documents = []
                return self._documents
            for path in sorted(self.root.rglob("*.md")):
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                docs.append((path, text))
            self._documents = docs
        return self._documents

    def find(
        self, literal_terms: Sequence[str], pattern: re.Pattern[str] | None
    ) -> Path | None:
        """Locate the first documentation file matching the provided criteria."""

        for path, text in self.documents:
            if any(term and term in text for term in literal_terms):
                return path
            if pattern and pattern.search(text):
                return path
        return None


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments for the documentation coverage checker.

    Args:
        argv: Raw command-line arguments to parse.

    Returns:
        Parsed argument namespace describing the desired input set.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate that touched backend Python and frontend Vue files have "
            "accompanying documentation."
        )
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged changes (git diff --cached).",
    )
    selection.add_argument(
        "--changed-since",
        metavar="REV",
        help="Inspect files changed since the provided git revision.",
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="Scan the entire repository for backend/frontend files requiring docs.",
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="*",
        help="Specific files or directories to verify.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit results as JSON for machine consumption.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print coverage details for documented files.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI entrypoint for the documentation coverage checker.

    Args:
        argv: Optional explicit argument list (defaults to ``sys.argv``).

    Returns:
        Process exit code. ``0`` indicates success, ``1`` signals missing
        documentation, and ``2`` represents an unexpected git error.
    """
    args = parse_args(argv or sys.argv[1:])

    try:
        targets = resolve_target_files(args)
    except subprocess.CalledProcessError as exc:
        print(f"[docs] Failed to resolve git files: {exc}", file=sys.stderr)
        return 2

    filtered = filter_relevant_files(targets)
    if not filtered:
        if not args.json_output:
            print("[docs] No backend/frontend Python or Vue files to verify.")
        else:
            print(json.dumps({"checked": [], "missing": []}, indent=2))
        return 0

    corpora = {name: DocCorpus(path) for name, path in DOC_ROOTS.items()}
    results = [check_file(path, corpora) for path in filtered]

    missing = [result for result in results if not result.is_documented]
    covered = [result for result in results if result.is_documented]

    if args.json_output:
        payload = {
            "checked": [
                {
                    "file": result.file_path.as_posix(),
                    "category": result.category,
                    "documentation": result.doc_path.as_posix()
                    if result.doc_path
                    else None,
                    "message": result.message,
                }
                for result in results
            ],
            "missing": [
                {
                    "file": result.file_path.as_posix(),
                    "category": result.category,
                    "message": result.message,
                }
                for result in missing
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if covered and args.verbose:
            print("[docs] Verified documentation:")
            for result in covered:
                if result.doc_path is None:  # pragma: no cover - defensive
                    continue
                doc_rel = result.doc_path.relative_to(REPO_ROOT)
                source_path = result.file_path.as_posix()
                doc_target = doc_rel.as_posix()
                print(f"  • {source_path} → {doc_target}")
        if missing:
            print("[docs] Missing documentation for:")
            for result in missing:
                print(f"  • {result.file_path.as_posix()} ({result.message})")
        else:
            print(f"[docs] Verified documentation for {len(covered)} file(s).")

    return 1 if missing else 0


def resolve_target_files(args: argparse.Namespace) -> list[Path]:
    """Compute the candidate files to inspect based on the provided options.

    Args:
        args: Parsed CLI options controlling file selection.

    Returns:
        Repository-relative paths that should be evaluated.
    """
    if args.paths:
        paths: list[Path] = []
        for raw in args.paths:
            candidate = (
                (REPO_ROOT / raw).resolve()
                if not Path(raw).is_absolute()
                else Path(raw)
            )
            if candidate.is_dir():
                for child in candidate.rglob("*"):
                    if not child.is_file():
                        continue
                    try:
                        rel_child = child.relative_to(REPO_ROOT)
                    except ValueError:
                        continue
                    paths.append(rel_child)
                continue
            try:
                rel = candidate.relative_to(REPO_ROOT)
            except ValueError:
                rel = Path(raw)
            paths.append(rel)
        return paths

    if args.staged:
        return _git_ls(["diff", "--cached", "--name-only", "--diff-filter=ACMRT"])
    if args.changed_since:
        return _git_ls(
            [
                "diff",
                f"{args.changed_since}..HEAD",
                "--name-only",
                "--diff-filter=ACMRT",
            ]
        )
    if args.all:
        return list_all_repo_files()

    # Default to staged changes when no explicit selection is provided.
    return _git_ls(["diff", "--cached", "--name-only", "--diff-filter=ACMRT"])


def _git_ls(arguments: Sequence[str]) -> list[Path]:
    """Return repository-relative paths reported by a git command.

    Args:
        arguments: Argument list to pass to ``git``.

    Returns:
        Paths from git stdout converted to ``Path`` objects.
    """
    result = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = [Path(line) for line in result.stdout.splitlines() if line.strip()]
    return paths


def list_all_repo_files() -> list[Path]:
    """Enumerate backend and frontend files tracked in the repository.

    Returns:
        Repository-relative paths for files under ``backend/`` and ``frontend/``.
    """
    candidates: list[Path] = []
    for category in ("backend", "frontend"):
        base = REPO_ROOT / category
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                try:
                    rel = path.relative_to(REPO_ROOT)
                except ValueError:
                    continue
                candidates.append(rel)
    return candidates


def filter_relevant_files(paths: Iterable[Path]) -> list[Path]:
    """Filter the provided paths down to backend/frontend Python and Vue files.

    Args:
        paths: Candidate repository-relative paths to evaluate.

    Returns:
        Sorted list of files eligible for documentation checks.
    """
    relevant: set[Path] = set()
    for path in paths:
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if not path.parts:
            continue
        prefix = path.parts[0]
        if prefix not in DOC_ROOTS:
            continue
        # Normalize to repo-relative Path with forward slashes for reporting.
        normalized = Path("/").joinpath(*path.parts).relative_to("/")
        relevant.add(normalized)
    return sorted(relevant)


def check_file(path: Path, corpora: dict[str, DocCorpus]) -> FileDocResult:
    """Determine whether a backend/frontend source file has documentation coverage.

    Args:
        path: Repository-relative path to the source file.
        corpora: Mapping of documentation corpora keyed by category name.

    Returns:
        Coverage result describing the located documentation (if any).
    """
    category = path.parts[0]
    doc_root = DOC_ROOTS[category]
    corpus = corpora[category]

    relative = Path(*path.parts[1:]) if len(path.parts) > 1 else Path(path.name)
    literal_terms = build_literal_terms(category, relative)

    word_pattern: re.Pattern[str] | None = None
    base_name = relative.stem
    if re.search(r"[A-Z_]", base_name):
        word_pattern = re.compile(rf"\b{re.escape(base_name)}\b")

    doc_path = corpus.find(literal_terms, word_pattern)
    if doc_path:
        return FileDocResult(file_path=path, category=category, doc_path=doc_path)

    message = (
        f"no reference in docs/{category}"
        if doc_root.exists()
        else "documentation tree missing"
    )
    return FileDocResult(
        file_path=path, category=category, doc_path=None, message=message
    )


def build_literal_terms(category: str, relative: Path) -> list[str]:
    """Build literal search terms that might appear in documentation.

    Args:
        category: Top-level directory for the source file (``backend`` or ``frontend``).
        relative: Path relative to the category root for the source file.

    Returns:
        Literal strings to probe within the documentation corpus.
    """
    path_with_prefix = Path(category) / relative
    literals = {
        relative.as_posix(),
        path_with_prefix.as_posix(),
    }
    file_name = relative.name
    literals.add(file_name)
    literals.add(f"`{file_name}`")
    literals.add(f"`{relative.as_posix()}`")
    literals.add(f"`{path_with_prefix.as_posix()}`")

    if file_name.endswith(".py"):
        module_path = relative.with_suffix("")
        dotted = ".".join(module_path.parts)
        literals.add(dotted)
        literals.add(f"`{dotted}`")

    return [literal for literal in literals if literal]


if __name__ == "__main__":
    sys.exit(main())
