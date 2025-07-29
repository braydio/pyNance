# **File-to-Step Map: Dashboard.vue UX/UI Overhaul**

### **Legend:**

- **\[D]** = `frontend/src/views/Dashboard.vue`
- **\[AL]** = `frontend/src/components/layout/AppLayout.vue`
- **\[TAS]** = `frontend/src/components/widgets/TopAccountSnapshot.vue`
- **\[DNC]** = `frontend/src/components/charts/DailyNetChart.vue`
- **\[CBC]** = `frontend/src/components/charts/CategoryBreakdownChart.vue`
- **\[CWTB]** = `frontend/src/components/ui/ChartWidgetTopBar.vue`
- **\[AS]** = `frontend/src/components/widgets/AccountSnapshot.vue`
- **\[AT]** = `frontend/src/components/tables/AccountsTable.vue`
- **\[TT]** = `frontend/src/components/tables/TransactionsTable.vue`
- **\[PC]** = `frontend/src/components/tables/PaginationControls.vue`
- **\[TM]** = `frontend/src/components/modals/TransactionModal.vue`
- **\[GCD]** = `frontend/src/components/ui/GroupedCategoryDropdown.vue`
- **\[UTIL]** = Any utility/composable used for data, formatting, etc. (e.g. `/frontend/src/composables`, `/utils/format.js`)
- **\[README]** = `frontend/src/views/README.md` (or equivalent)

---

## **Phase 1: Audit & Documentation**

**1.1. Automated UI/UX Audit**

- Files:

  - \[D], \[AL], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD]
  - _(UI audit = visual/code review for every direct child component)_

**1.2. Code Audit**

- Files:

  - \[D], \[AL], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD], \[UTIL]
  - _(Props, emits, data flow—trace through all component code)_

**1.3. Create Baseline Documentation**

- Files:

  - \[D] (add JSDoc/comments)
  - \[README] (create/update with Dashboard map)
  - \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD] (add JSDoc/prop docs where missing)

---

## **Phase 2: Layout, Spacing & Responsiveness**

**2.1. Responsive Layout Refactor**

- Files:

  - \[D] (main layout)
  - \[AL] (outer layout, global responsiveness)
  - \[TAS], \[DNC], \[CBC], \[AS] (card structure, chart wrappers)

**2.2. Spacing/Styling Pass**

- Files:

  - \[D], \[AL], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD]
  - _(Any with margin/padding, box, card elements)_

**2.3. Scroll & Sticky Elements**

- Files:

  - \[D] (table/modal sections)
  - \[AT], \[TT] (table scroll/sticky headers)
  - \[TM] (modal scroll handling)

---

## **Phase 3: Components, Slots, and Best Practices**

**3.1. Props Validation & Defaults**

- Files:

  - \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD]
  - \[D] (ensure all child usage is with valid props/emit)

**3.2. Scoped Slots/Reusable Headers**

- Files:

  - \[D] (refactor slot use)
  - \[CWTB] (if converted to `<CardHeader>`)
  - _Potential new_: `frontend/src/components/ui/CardHeader.vue`

**3.3. Extract Logic & UI**

- Files:

  - \[D] (move data/API logic out, break up UI blocks)
  - \[UTIL] (create/move logic to `/composables/useDashboardData.js` or similar)
  - \[AT], \[TT], \[TM] (if large blocks are split)

---

## **Phase 4: Accessibility & Feedback**

**4.1. Accessibility Fixes**

- Files:

  - \[D], \[AL], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD]

**4.2. Color & Contrast Audit**

- Files:

  - \[D], \[TAS], \[DNC], \[CBC], \[AS], \[AT], \[TT], \[TM]
  - _Plus_ theme/CSS vars as needed

**4.3. Loading, Error, Empty States**

- Files:

  - \[D], \[TAS], \[DNC], \[CBC], \[AS], \[AT], \[TT], \[PC], \[TM]

---

## **Phase 5: Enhanced Interactions**

**5.1. UI/UX Interactions**

- Files:

  - \[D] (expand/collapse logic)
  - \[AT], \[TT], \[TM] (transitions, icons for toggle, tooltip)
  - \[CWTB] (control tooltips if present)

**5.2. Chart/Data Improvements**

- Files:

  - \[DNC], \[CBC], \[D] (pass dynamic date range down)

**5.3. State Persistence**

- Files:

  - \[D] (localStorage for UI state)
  - \[UTIL] (if helper created for persistence)

---

## **Phase 6: Code Cleanup & Reliability**

**6.1. Refactor Logic**

- Files:

  - \[D], \[UTIL] (break up, move logic, refactor)

**6.2. Error Handling**

- Files:

  - \[D], \[UTIL], \[TAS], \[DNC], \[CBC], \[AS], \[AT], \[TT], \[TM] (wrap data/API calls)

---

## **Phase 7: Visual & Cosmetic Polish**

**7.1. Color & Typography Consistency**

- Files:

  - \[D], \[TAS], \[DNC], \[CBC], \[AS], \[AT], \[TT], \[TM], \[CWTB]
  - _Theme/CSS vars file if exists_

**7.2. Iconography**

- Files:

  - \[D], \[TAS], \[DNC], \[CBC], \[AS], \[AT], \[TT], \[TM], \[CWTB]
  - _Icon component or icon import/usage files_

---

## **Phase 8: Unpolished/Incomplete Features**

**8.1. Spending Insights Panel**

- Files:

  - \[D] (add placeholder/progress)

**8.2. Modal & Pagination Controls**

- Files:

  - \[TM] (modal a11y, esc, focus)
  - \[PC] (pagination controls)

---

## **Phase 9: Testing**

**9.1. Unit/Snapshot Tests**

- Files:

  - All: \[D], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD]
  - _Test files: `/frontend/tests/unit/_`, `/frontend/tests/components/_` (add/expand)_

---

## **Phase 10: Final Documentation & Review**

**10.1. Final Review**

- Files:

  - \[README], \[D] (final docs, audit comments)

---

# **Example Step Breakdown (Sample):**

**Phase 2.1 – Responsive Layout Refactor:**

- \[D]: Refactor grid layout of main dashboard page
- \[AL]: Ensure outer layout is responsive and not overriding child layouts
- \[TAS], \[DNC], \[CBC], \[AS]: Check for hardcoded widths, ensure containers/cards have responsive classes

**Phase 3.3 – Extract Logic & UI:**

- \[D]: Move logic out, import from new composable
- \[UTIL]: Create/modify `useDashboardData.js`
- \[AT], \[TT]: If tables get large, split table into subcomponents or views

---

# **Summary Table (Steps-to-Files):**

| Step     | Files to Change/Review                                                                           |
| -------- | ------------------------------------------------------------------------------------------------ |
| 1.1, 1.2 | \[D], \[AL], \[TAS], \[DNC], \[CBC], \[CWTB], \[AS], \[AT], \[TT], \[PC], \[TM], \[GCD], \[UTIL] |
| 1.3      | All above + \[README]                                                                            |
| 2.1      | \[D], \[AL], \[TAS], \[DNC], \[CBC], \[AS]                                                       |
| 2.2, 2.3 | All UI components                                                                                |
| 3.1      | All components w/ props                                                                          |
| 3.2      | \[D], \[CWTB], _potential new \[CardHeader]_                                                     |
| 3.3      | \[D], \[UTIL], \[AT], \[TT], \[TM]                                                               |
| 4.x      | All UI components, focus on \[D], \[AL], \[TT], \[AT], \[TM]                                     |
| 5.x      | \[D], \[TT], \[AT], \[TM], \[CWTB], \[UTIL]                                                      |
| 6.x      | \[D], \[UTIL], all API/data handling components                                                  |
| 7.x      | All UI components, \[theme/CSS]                                                                  |
| 8.x      | \[D], \[TM], \[PC]                                                                               |
| 9.x      | All, add/expand `/tests/unit`                                                                    |
| 10.x     | \[D], \[README]                                                                                  |

---

## **How to Use This List:**

- **Before each step**, review and list all affected files.
- **Each PR/change** should clearly reference the files/sections changed.
- **If a new utility, icon, or CardHeader component is created,** add it to the relevant phase and update the documentation.
