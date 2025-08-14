# pyNance Repository Migration Plan
## File Reorganization Mapping

This document provides a concrete mapping of current files to their target locations based on the repository conventions already present.

Generated on: $(date)

---

## 1. Keep at Root Level

### Files that stay in place:
- **README.md** → ✅ Keep (already correctly located)
- **CHANGELOG.md** → ⚠️ MISSING - Needs to be created

### Files requiring renaming:
- **CONTRIBUTING.md** → **CONTRIBUTING.md** (rename and keep at root as standard contributor guide)

---

## 2. Move to docs/ Structure

### Process Documentation:
- **docs/process/repo_organization.md** → **docs/process/repo_organization.md**

### Frontend Documentation:
- **docs/frontend/Consolidated_TODO.md** → **docs/frontend/Consolidated_TODO.md**
- **docs/frontend/PHASES.md** → **docs/frontend/PHASES.md**

### Architecture Documentation (existing files to organize):
- **docs/architecture/01_DEV-ArchitectureChecks.md** → ✅ Keep in place (already correctly located)
- **docs/architecture/Plaid_Helpers_Design.md** → ✅ Keep in place (already correctly located)
- **docs/internal/architecture/arch_ux_02.md** → **docs/architecture/arch_ux_02.md**
- **docs/process/architecture_notes.md** → **docs/architecture/architecture_notes.md**

### Maps and Integration Documentation:
- **docs/maps/backend_map.txt** → ✅ Keep in place (already correctly located)
- **docs/maps/frontend_map.txt** → ✅ Keep in place (already correctly located)
- **docs/maps/link_account_products_map.md** → ✅ Keep in place (already correctly located)

### Developer Notes and Scratch Pads:
- **docs/internal/Dev_ForecastReference.md** → **docs/devnotes/Dev_ForecastReference.md**
- **docs/internal/DevelopingForecast.txt** → **docs/devnotes/DevelopingForecast.txt**
- **docs/internal/refresh_route_reviewer.md** → **docs/devnotes/refresh_route_reviewer.md**
- **docs/internal/Retrospective_Mapping.md** → **docs/devnotes/Retrospective_Mapping.md**

### Maintenance Documentation:
- **docs/maintenance/cleanup_checklist.md** → ✅ Keep in place (already correctly located)

---

## 3. Files to Remove or Merge

### Potential Duplicates Analysis:
Based on repository scan, the following files mentioned in cleanup_checklist.md were not found:
- **README2md** - NOT FOUND (may have been already removed)
- **DevelopingForecastEnging.txt** - NOT FOUND (may have been already removed)

### Multiple TODO Files to Consolidate:
- **NewToDo.md** → Merge unique content into **docs/frontend/Consolidated_TODO.md**, then remove
- **ToDo.md** → Merge unique content into **docs/frontend/Consolidated_TODO.md**, then remove  
- **WarpToDo.md** → Merge unique content into **docs/frontend/Consolidated_TODO.md**, then remove
- **docs/TODO.md** → Merge unique content into **docs/frontend/Consolidated_TODO.md**, then remove
- **docs/ToDoCodex.md** → Merge unique content into **docs/frontend/Consolidated_TODO.md**, then remove

### Other Files for Review:
- **Phase_1.md** → Content review for merge into **docs/frontend/PHASES.md**, then remove if superseded
- **ProcessLegend.md** → Content review for merge into **docs/frontend/PHASES.md**, then remove if superseded  
- **ReviewKey.md** → Content review for merge into **docs/frontend/Consolidated_TODO.md**, then remove if superseded

---

## 4. Directory Structure Creation

### New directories to create:
```bash
mkdir -p docs/process
mkdir -p docs/devnotes
# docs/architecture/ already exists
# docs/maps/ already exists
# docs/maintenance/ already exists
# docs/frontend/ already exists
```

---

## 5. Detailed Migration Commands

### Phase 1: Create missing directories
```bash
mkdir -p docs/process docs/devnotes
```

### Phase 2: Rename files
```bash
mv CONTRIBUTING.md CONTRIBUTING.md
```

### Phase 3: Move files to target locations
```bash
# Process documentation
mv docs/process/repo_organization.md docs/process/repo_organization.md

# Frontend documentation  
mv docs/frontend/Consolidated_TODO.md docs/frontend/Consolidated_TODO.md
mv docs/frontend/PHASES.md docs/frontend/PHASES.md

# Architecture reorganization
mv docs/internal/architecture/arch_ux_02.md docs/architecture/arch_ux_02.md
mv docs/process/architecture_notes.md docs/architecture/architecture_notes.md

# Developer notes
mv docs/internal/Dev_ForecastReference.md docs/devnotes/Dev_ForecastReference.md
mv docs/internal/DevelopingForecast.txt docs/devnotes/DevelopingForecast.txt
mv docs/internal/refresh_route_reviewer.md docs/devnotes/refresh_route_reviewer.md
mv docs/internal/Retrospective_Mapping.md docs/devnotes/Retrospective_Mapping.md
```

### Phase 4: Merge and remove duplicate TODOs (manual review required)
```bash
# These require manual content review and merging:
# - NewToDo.md → docs/frontend/Consolidated_TODO.md
# - ToDo.md → docs/frontend/Consolidated_TODO.md  
# - WarpToDo.md → docs/frontend/Consolidated_TODO.md
# - docs/TODO.md → docs/frontend/Consolidated_TODO.md
# - docs/ToDoCodex.md → docs/frontend/Consolidated_TODO.md

# After merging unique content:
# rm NewToDo.md ToDo.md WarpToDo.md docs/TODO.md docs/ToDoCodex.md
```

### Phase 5: Create missing files
```bash
# Create CHANGELOG.md if it doesn't exist
touch CHANGELOG.md
echo "# Changelog\n\nAll notable changes to this project will be documented in this file.\n" > CHANGELOG.md
```

### Phase 6: Clean up empty directories
```bash
# Remove empty internal directory if all files moved
if [ -z "$(ls -A docs/internal)" ]; then
    rmdir docs/internal
fi
```

---

## 6. Verification Checklist

After migration, verify:
- [ ] **CONTRIBUTING.md** exists at root (renamed from CONTRIBUTING.md)
- [ ] **CHANGELOG.md** exists at root
- [ ] **docs/process/repo_organization.md** exists (moved from docs/process/repo_organization.md)
- [ ] **docs/frontend/Consolidated_TODO.md** exists (moved from root)
- [ ] **docs/frontend/PHASES.md** exists (moved from root)
- [ ] **docs/architecture/** contains consolidated architecture docs
- [ ] **docs/devnotes/** contains consolidated developer notes
- [ ] **docs/maps/** structure preserved (already correct)
- [ ] **docs/maintenance/cleanup_checklist.md** preserved (already correct)
- [ ] No duplicate TODO files remain
- [ ] All unique content from merged files preserved

---

## 7. Risk Assessment

### Low Risk:
- Moving documentation files to docs/ subdirectories
- Renaming CONTRIBUTING.md to CONTRIBUTING.md
- Creating missing CHANGELOG.md

### Medium Risk:
- Merging multiple TODO files (risk of losing unique content)
- Removing "duplicate" files without thorough content comparison

### Mitigation:
- Perform content diff on all files before merging
- Create backup branch before executing migration
- Review merged content with stakeholders before removing originals

---

## 8. Post-Migration Tasks

After executing migration:
- [ ] Update any hardcoded file paths in documentation
- [ ] Update README.md references to moved files
- [ ] Test that all cross-references still work
- [ ] Update any automation scripts that reference old paths
- [ ] Create redirect notices in moved file locations if needed

---

*This migration plan should be executed in phases with testing at each step to ensure no content or functionality is lost.*
