## 📘 `import_helpers.py`
```markdown
# Import Helpers

Provides `dispatch_import()` to route uploaded files to the appropriate parser.
Supports CSV transaction imports (Synchrony CSV export format) and PDF imports
using `pdfplumber` to read Synchrony statements.

**Dependencies**: `csv`, `datetime`, `pdfplumber`, `app.config.logger`.
```
