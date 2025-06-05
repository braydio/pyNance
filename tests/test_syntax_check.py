import ast
import pathlib
import tokenize


def test_all_python_files_syntax_ok():
    for path in pathlib.Path("backend").rglob("*.py"):
        if path.name.startswith("__"):  # skip __init__.py etc.
            continue
        with tokenize.open(path) as file:
            source = file.read()

        ast.parse(source, filename=str(path))
