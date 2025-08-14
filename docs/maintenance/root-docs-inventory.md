# Root-Level Documentation Inventory and Classification

**Generated:** January 2025  
**Purpose:** Comprehensive inventory of root-level documentation with classification and proposed organization

## Complete Inventory of Root-Level Documentation Files

### **Markdown Documentation (21 files)**
1. `Accounts_Dev_Plan.md` - Development plan for accounts component
2. `AGENTS.md` - Contributor guide for short-term agents 
3. `CLAUDE.md` - Project developer guide (duplicate of CODEX.md)
4. `CODEX.md` - Project developer guide (duplicate of CLAUDE.md)
5. `COMPONENT_ACCOUNTS.md` - Unified accounts component specification
6. `CONSOLIDATED_DASHBOARD.md` - Consolidated dashboard component tasks
7. `Consolidated_TODO.md` - Master consolidated TODO file
8. `CONSOLIDATION_INVENTORY.md` - Source files inventory for consolidation
9. `DEV_GUIDE.md` - Comprehensive development standards guide
10. `GITHUB_ISSUE_TEMPLATE.md` - Template for GitHub issues
11. `LEGACY_DEPRECATION_TEMPLATE.md` - Template for deprecating legacy files
12. `NewToDo.md` - Frontend site map and issue tracker
13. `ORGANIZE.md` - Full repository organization plan
14. `Phase_1.md` - Detailed Phase 1 audit specifications
15. `PHASES.md` - Complete 10-phase implementation plan
16. `PR_DESCRIPTION_TEMPLATE.md` - Pull request description template
17. `ProcessLegend.md` - Step-by-step execution plan for dashboard improvements
18. `README.md` - Main project documentation (setup and overview)
19. `ReviewKey.md` - Master tracker combining FileLegend and ProcessLegend
20. `ToDo.md` - Frontend site map and issue tracker (older version)
21. `WarpToDo.md` - Specific widget improvement tasks

### **Text Documentation (1 file)**
22. `Exprot_Claude_Erroring.txt` - Claude Code session log with styling updates

### **Configuration Files (3 files)**
23. `requirements-dev.txt` - Python development dependencies
24. `requirements-slim.txt` - Slim Python requirements  
25. `requirements.txt` - Full Python dependencies

---

## Classification and Proposed Actions

### **KEEP AT ROOT**
**Core project files that serve as entry points:**

1. **`README.md`** - ✅ **KEEP AT ROOT**
   - **Purpose:** Main project documentation, setup guide, architecture overview
   - **Justification:** Primary entry point for developers, contains essential setup information

2. **`DEV_GUIDE.md`** - ✅ **KEEP AT ROOT** 
   - **Purpose:** Comprehensive development standards, tooling, validation
   - **Justification:** Critical reference for all contributors, frequently accessed

3. **`ORGANIZE.md`** - ✅ **KEEP AT ROOT**
   - **Purpose:** High-level repository organization plan
   - **Justification:** Strategic document for repository structure

4. **Configuration files** - ✅ **KEEP AT ROOT**
   - `requirements.txt`, `requirements-dev.txt`, `requirements-slim.txt`
   - **Purpose:** Python dependency management
   - **Justification:** Standard location for dependency files

### **MOVE TO docs/process/**
**Process and workflow documentation:**

5. **`PHASES.md`** → **`docs/process/implementation-phases.md`**
   - **Purpose:** 10-phase implementation plan for dashboard improvements
   - **Justification:** Process documentation for development workflow

6. **`ProcessLegend.md`** → **`docs/process/execution-plan.md`**
   - **Purpose:** Step-by-step execution plan for dashboard UX/UI improvements
   - **Justification:** Detailed process documentation

7. **`AGENTS.md`** → **`docs/process/contributor-guide.md`**
   - **Purpose:** Contributor guide for short-term agents
   - **Justification:** Process documentation for contributors

8. **`GITHUB_ISSUE_TEMPLATE.md`** → **`docs/process/github-templates.md`**
   - **Purpose:** Template for GitHub issues
   - **Justification:** Process documentation for issue management

9. **`PR_DESCRIPTION_TEMPLATE.md`** → **`docs/process/pr-templates.md`**
   - **Purpose:** Pull request description template
   - **Justification:** Process documentation for PR management

10. **`LEGACY_DEPRECATION_TEMPLATE.md`** → **`docs/process/legacy-migration.md`**
    - **Purpose:** Template for deprecating legacy files
    - **Justification:** Process documentation for file organization

### **MOVE TO docs/frontend/**
**Frontend-specific component and development documentation:**

11. **`CONSOLIDATED_DASHBOARD.md`** → **`docs/frontend/dashboard-component-spec.md`**
    - **Purpose:** Consolidated dashboard component tasks and specifications
    - **Justification:** Frontend component documentation

12. **`COMPONENT_ACCOUNTS.md`** → **`docs/frontend/accounts-component-spec.md`**
    - **Purpose:** Unified accounts component specification
    - **Justification:** Frontend component documentation

13. **`Accounts_Dev_Plan.md`** → **`docs/frontend/accounts-development-plan.md`**
    - **Purpose:** Development plan for accounts component
    - **Justification:** Frontend development planning

14. **`Phase_1.md`** → **`docs/frontend/phase-1-audit-details.md`**
    - **Purpose:** Detailed Phase 1 audit specifications
    - **Justification:** Frontend audit documentation

15. **`ReviewKey.md`** → **`docs/frontend/component-review-tracker.md`**
    - **Purpose:** Master tracker combining FileLegend and ProcessLegend
    - **Justification:** Frontend component tracking

### **MOVE TO docs/maintenance/**
**Maintenance and organization documentation:**

16. **`Consolidated_TODO.md`** → **`docs/maintenance/master-todo.md`**
    - **Purpose:** Master consolidated TODO file
    - **Justification:** Maintenance tracking documentation

17. **`CONSOLIDATION_INVENTORY.md`** → **`docs/maintenance/file-consolidation-inventory.md`**
    - **Purpose:** Source files inventory for consolidation
    - **Justification:** Maintenance documentation for file organization

18. **`WarpToDo.md`** → **`docs/maintenance/widget-improvements.md`**
    - **Purpose:** Specific widget improvement tasks
    - **Justification:** Maintenance task tracking

### **REMOVE OR MERGE**
**Duplicate, outdated, or temporary files:**

19. **`CLAUDE.md`** - 🗑️ **REMOVE** (duplicate of CODEX.md)
    - **Justification:** Identical content to CODEX.md, causes confusion

20. **`CODEX.md`** - 🗑️ **MERGE INTO DEV_GUIDE.md** or **REMOVE**
    - **Purpose:** Project developer guide (basic setup commands)
    - **Justification:** Content overlaps with README.md and DEV_GUIDE.md

21. **`NewToDo.md`** - 🗑️ **MERGE INTO docs/maintenance/master-todo.md**
    - **Purpose:** Frontend site map and issue tracker
    - **Justification:** Superseded by Consolidated_TODO.md

22. **`ToDo.md`** - 🗑️ **MERGE INTO docs/maintenance/master-todo.md**
    - **Purpose:** Older version of frontend issue tracker
    - **Justification:** Superseded by newer TODO files

23. **`Exprot_Claude_Erroring.txt`** - 🗑️ **REMOVE**
    - **Purpose:** Claude Code session log with styling updates
    - **Justification:** Temporary development artifact, not documentation

---

## Migration Plan Summary

### **Files Staying at Root (4 files):**
- `README.md` - Main project entry point
- `DEV_GUIDE.md` - Developer standards guide  
- `ORGANIZE.md` - Repository organization plan
- Configuration files (`requirements*.txt`)

### **Files Moving to docs/ (14 files):**
- **docs/process/ (6 files):** Process and workflow documentation
- **docs/frontend/ (5 files):** Frontend component specifications
- **docs/maintenance/ (3 files):** Maintenance and TODO tracking

### **Files to Remove/Merge (5 files):**
- Remove duplicates (CLAUDE.md)
- Merge outdated TODOs into master TODO
- Remove temporary artifacts (Exprot_Claude_Erroring.txt)
- Consolidate overlapping content (CODEX.md)

### **docs/index/INDEX.md Status:**
✅ **EXISTS** - Documentation index file is present and can be updated to reflect new organization

---

## Next Steps

1. **Create target directories** in docs/ structure
2. **Move files** according to classification above
3. **Update docs/index/INDEX.md** with new file locations
4. **Add deprecation notices** to files being moved/removed
5. **Update cross-references** in remaining files
6. **Test documentation links** and navigation

This organization will create a cleaner root directory while preserving all documentation in logical, discoverable locations within the docs/ hierarchy.
