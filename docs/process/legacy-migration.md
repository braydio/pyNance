# Legacy File Deprecation Template

This template shows how to add deprecation notices to the legacy TODO files as outlined in [LEGACY_MAP].

## Template for NewToDo.md

Add this at the very top of `NewToDo.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Dashboard UX/UI Issues → See [COMPONENT_DASHBOARD] section
> - Component Tasks → See [COMPONENT_TASKS] section
> - Global Dashboard TODOs → See [GLOBAL_DASHBOARD] section
> - Mock Components → See [COMPONENT_MOCK_DIR] section

---
```

## Template for ToDo.md

Add this at the very top of `ToDo.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Site-Wide Features, Components, and Tasks → See [COMPONENT_TASKS] section
> - Dashboard Components → See [COMPONENT_DASHBOARD] section
> - View Components → Distributed across [COMPONENT_TASKS] sections

---
```

## docs/TODO.md Removal

docs/TODO.md has been removed; see `docs/frontend/Consolidated_TODO.md` for the unified task list.

## Template for Phase_1.md

Add this at the very top of `Phase_1.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Phase 1 detailed specifications → See [PHASES] Phase 1 section
> - File mapping → See [STEPS_TO_FILES] section

---
```

## Template for ProcessLegend.md

Add this at the very top of `ProcessLegend.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - 10-Phase Implementation Plan → See [PHASES] section
> - Phase-to-Files Mapping → See [STEPS_TO_FILES] section
> - Execution Guidelines → Integrated throughout sections

---
```

## Template for ReviewKey.md

Add this at the very top of `ReviewKey.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Component Legend → See [LEGEND_MAP] section
> - Phase-to-Files Mapping → See [STEPS_TO_FILES] section
> - Review Guidelines → Integrated in [PHASES] sections

---
```

## Template for FileLegend.md

Add this at the very top of `FileLegend.md`:

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Component Tags → See [LEGEND_MAP] section
> - Steps-to-Files Mapping → See [STEPS_TO_FILES] section
> - Phase File Mapping → Integrated in [STEPS_TO_FILES] section

---
```

## Instructions for Implementation

1. Copy the appropriate template above to the top of each legacy file
2. Adjust the relative path to TODO.md based on file location:
   - For root-level files: `../frontend/Consolidated_TODO.md`
   - For files in docs/: `../frontend/Consolidated_TODO.md`
3. Ensure all section ID references ([COMPONENT_DASHBOARD], etc.) are accurate
4. Test that all links work correctly
5. Commit these changes as part of the deprecation PR

## Verification Steps

After adding deprecation notices:

- [ ] Verify all links point to the correct consolidated TODO.md
- [ ] Confirm all section IDs exist in the consolidated file
- [ ] Test navigation between legacy files and consolidated sections
- [ ] Ensure deprecation notices are prominently visible
- [ ] Check that mapping descriptions are accurate
