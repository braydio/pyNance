# Documentation Guidelines

This guide applies to files under `docs/`.

## Structure

- Use `docs/index/INDEX.md` as the canonical entry point for navigation; update it when moving or adding docs.
- Store architecture notes in `docs/architecture/` and process/workflow material in `docs/process/`.
- Place developer scratch notes and working references in `docs/devnotes/`.
- Keep frontend and backend feature docs under `docs/frontend/` and `docs/backend/` respectively.

## Front Matter

- Many backend docs use a front matter header with Owner, Last Updated, and Status.
- If you edit a file that already has front matter, update the `Last Updated` date accordingly.

## File Moves

- When moving documentation, update any cross-links and the index.
- Remove empty directories after migrations to keep the tree tidy.

## Reference Hygiene

- Prefer relative links within `docs/`.
- Keep file names stable when possible; if you must rename, add an entry to `docs/index/INDEX.md`.
