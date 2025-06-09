import os
import ast


def chunk_text(text, max_length=1000):
    """
    Split input text into contiguous blocks, capped at roughly `max_length` characters.
    Lines are preserved in order, and splitting is done on line boundaries to avoid mid-sentence truncation.
    """
    lines = text.splitlines()
    chunks, current, current_len = [], [], 0

    for line in lines:
        # If adding this line exceeds the chunk limit, start a new chunk
        if current_len + len(line) > max_length:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("\n".join(current))

    return chunks


def extract_metadata(path, content):
    """
    Extract structured metadata from a file, based on its extension and contents.
    Metadata includes:
        - full path
        - relative path (from backend/)
        - file extension
        - semantic tags (function/class names in .py, headings in .md)
        - top-level docstring summary (if applicable)
    """
    ext = os.path.splitext(path)[1]
    rel_path = os.path.relpath(path, start="backend")
    tags = set()
    docstrings = []

    if ext == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    tags.add(node.name)
                    doc = ast.get_docstring(node)
                    if doc:
                        docstrings.append(doc)
        except Exception:
            pass

    elif ext == ".md":
        tags.update(
            line.strip("# *").strip()
            for line in content.splitlines()
            if line.strip().startswith("#")
        )

    return {
        "source": path,
        "relative_path": rel_path,
        "ext": ext,
        "tags": sorted(tags),
        "docstring_summary": docstrings[0] if docstrings else "",
    }
