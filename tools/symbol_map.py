#!/usr/bin/env python3
"""Generate a symbol map for source files using Tree-sitter.

This utility scans Python, TypeScript, JavaScript and TSX files in a
repository and outputs a JSON structure describing the top-level
functions, classes and methods found in each file. The symbol map helps
agents maintain context about the codebase for refactoring and
navigation tasks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from tree_sitter import Parser
from tree_sitter_languages import get_language

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".js": "javascript",
    ".tsx": "tsx",
}

TARGET_TYPES = {"function_definition", "class_definition", "method_definition"}


def sym_map(path: Path) -> List[Dict[str, Any]]:
    """Return a list of symbol metadata for ``path``.

    Parameters
    ----------
    path:
        Source file to inspect.

    Returns
    -------
    list of dict
        Each item describes a discovered symbol with its kind, name,
        location and a snippet limited to 4,000 characters.
    """

    lang_name = LANGUAGE_BY_SUFFIX.get(path.suffix)
    if lang_name is None:
        return []

    parser = Parser()
    parser.set_language(get_language(lang_name))

    src = path.read_bytes()
    tree = parser.parse(src)
    out: List[Dict[str, Any]] = []

    def walk(node: Any) -> None:
        if node.type in TARGET_TYPES:
            snippet = src[node.start_byte : node.end_byte].decode("utf-8", "ignore")
            ident = next(
                (c.text.decode() for c in node.children if c.type == "identifier"),
                "",
            )
            out.append(
                {
                    "kind": node.type,
                    "name": ident,
                    "start": node.start_point,
                    "end": node.end_point,
                    "snippet": snippet[:4000],
                }
            )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return out


def build_map(repo: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Construct a symbol map for all supported files under ``repo``."""
    files = [p for p in repo.rglob("*") if p.suffix in LANGUAGE_BY_SUFFIX]
    return {str(p.relative_to(repo)): sym_map(p) for p in files}


def main() -> None:
    """Entry point for command-line usage."""
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    data = build_map(repo.resolve())
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
