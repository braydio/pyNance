# pyNance Documentation

This is the entry point for documentation.
See docs/index/INDEX.md for a categorized index.

Working notes and scratch references live under `docs/devnotes/`.

## Front matter standard

Key backend documentation (including `docs/backend/app/routes`) now starts with a
front matter block capturing ownership and freshness metadata:

```
---
Owner: Backend Team
Last Updated: YYYY-MM-DD
Status: Active
---
```

Keep the `Last Updated` date current when making substantial edits so the
front-matter linter can flag stale guides during CI.
