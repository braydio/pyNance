# scripts/chroma_support.py
import ast
import os


def chunk_text(text, max_length=1000):
    lines = text.splitlines()
    chunks, current, length = [], [], 0
    for line in lines:
        if length + len(line) > max_length:
            chunks.append("\n".join(current))
            current, length = [], 0
        current.append(line)
        length += len(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


def extract_functions(content):
    functions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
    except Exception:
        pass
    return functions


def extract_metadata(path, content):
    ext = os.path.splitext(path)[1]
    rel_path = os.path.relpath(path, start="backend")
    tags, docstrings = set(), []

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

    functions = extract_functions(content)
    return {
        "relative_path": rel_path,
        "file_extension": ext,
        "tags": ", ".join(sorted(tags)),
        "docstrings": " | ".join(docstrings),
        "functions": ", ".join(functions),
    }
