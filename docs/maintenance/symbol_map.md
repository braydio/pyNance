# Symbol Map Tool

`tools/symbol_map.py` builds a JSON index of top-level functions,
classes and methods for Python and TypeScript code. The output helps
maintenance agents quickly gather context about the codebase.

## Usage

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Generate a symbol map for the repository:

```bash
python tools/symbol_map.py . > symbols.json
```

The resulting `symbols.json` maps each source file to a list of symbols
with their type, name, location and a truncated snippet of the source
code.
