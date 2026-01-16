## 📘 `path_utils.py`

```markdown
# Path Utilities

Provides safe path resolution helpers that keep file access inside configured
backend directories. `resolve_path()` validates paths against the allowed
directory list, while `resolve_data_path()` anchors relative paths to the data
directory before validating them.

**Dependencies**: `pathlib`, `app.config.DIRECTORIES`.
```
