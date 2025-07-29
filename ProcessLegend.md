# **Step-by-Step Execution Plan: pyNance Dashboard.vue UX/UI Improvements**

---

## **Phase 1: Audit & Documentation (Foundation)**

**1.1. Automated UI/UX Audit**

- [ ] Use mobile emulation (e.g., Chrome DevTools) to visually audit Dashboard at multiple breakpoints (<600px, 768px, >1024px).
- [ ] Document every section’s spacing, card layout, overflow, and responsive behavior.

**1.2. Code Audit**

- [ ] List all props/emit events on imported components.
- [ ] Identify all “magic numbers” in Dashboard and its components.
- [ ] Inventory all direct API calls, data-fetch logic, and ref usage.

**1.3. Create Baseline Documentation**

- [ ] Add/Update JSDoc comments for each method, computed, and prop in Dashboard.vue.
- [ ] Begin or update a `README.md` with a component map and UX flows.

---

## **Phase 2: Layout, Spacing & Responsiveness**

**2.1. Responsive Layout Refactor**

- [ ] Convert major container layout to CSS Grid (if not already), ensuring main cards/widgets align at all sizes.
- [ ] Standardize all max/min width classes and review for consistency.

**2.2. Spacing/Styling Pass**

- [ ] Replace hardcoded paddings/margins with theme utility classes (Tailwind, etc.).
- [ ] Apply consistent border radius, shadow, and backgrounds to all top-level cards/panels.

**2.3. Scroll & Sticky Elements**

- [ ] Make table sections horizontally/vertically scrollable with sticky headers.
- [ ] Adjust modals to always fit within viewport with scroll if needed.

---

## **Phase 3: Components, Slots, and Best Practices**

**3.1. Props Validation & Defaults**

- [ ] Add `props` validation to all child components used (type, required, default).
- [ ] Add prop-shape JSDoc where passing objects/arrays.

**3.2. Scoped Slots/Reusable Headers**

- [ ] Refactor repeated control sections (above charts/tables) into a `<CardHeader>` reusable component with named slots for title, actions, and extra controls.

**3.3. Extract Logic & UI**

- [ ] Move all API/data-fetching logic into composables (e.g., `/composables/useDashboardData.js`).
- [ ] Extract expanded table/modal markup to their own view components if >150 lines.

---

## **Phase 4: Accessibility & Feedback**

**4.1. Accessibility Fixes**

- [ ] Add/verify `aria-labels`, keyboard navigation, and semantic HTML in all actionable controls.
- [ ] Add missing heading levels and semantic tags for each section/table.

**4.2. Color & Contrast Audit**

- [ ] Run a color contrast tool (e.g., Chrome Lighthouse, axe) and adjust variables for accessibility.
- [ ] Replace any fixed hex chart colors with color-blind-safe palette.

**4.3. Loading, Error, Empty States**

- [ ] Add skeleton loaders, loading spinners, and error catch blocks for each async section.
- [ ] Add friendly empty-states (with icon/message) for all lists/tables/charts.

---

## **Phase 5: Enhanced Interactions**

**5.1. UI/UX Interactions**

- [ ] Add animated transitions for table/modal expand/collapse.
- [ ] Use clear icons (chevron, plus/minus, etc.) for toggling expand/collapse.
- [ ] Add tooltips to unclear buttons and summary stats.

**5.2. Chart/Data Improvements**

- [ ] Allow users to select custom date ranges for charts (date picker).
- [ ] Add axis labels, legends, and context captions to all charts.

**5.3. State Persistence**

- [ ] Store expanded/collapsed UI states in localStorage or user profile if available.

---

## **Phase 6: Code Cleanup & Reliability**

**6.1. Refactor Logic**

- [ ] Break up large methods into smaller composables/functions.
- [ ] Remove dead/commented code, unused imports, and variables.
- [ ] Replace manual date manipulation with date-fns or dayjs everywhere.

**6.2. Error Handling**

- [ ] Add try/catch or `.catch` for all API calls with user-facing feedback.

---

## **Phase 7: Visual & Cosmetic Polish**

**7.1. Color & Typography Consistency**

- [ ] Replace all hardcoded colors with theme variables.
- [ ] Limit to 2-3 font sizes; ensure consistent font-weight and font-family.

**7.2. Iconography**

- [ ] Audit all icon usage; unify to one set and add icons for all key actions.

---

## **Phase 8: Unpolished/Incomplete Features**

**8.1. Spending Insights Panel**

- [ ] If incomplete, wrap in placeholder card with spinner/progress and a clear “coming soon” label.

**8.2. Modal & Pagination Controls**

- [ ] Ensure modals trap focus, close with Esc, and are accessible.
- [ ] Add loading/disabled states to all paginators.

---

## **Phase 9: Testing**

**9.1. Unit/Snapshot Tests**

- [ ] Add/expand test coverage for Dashboard.vue and new components/composables.
- [ ] Write tests for expanded/collapsed state, loading/error states, and data-fetching.

---

## **Phase 10: Final Documentation & Review**

**10.1. Final Review**

- [ ] Re-audit entire dashboard for mobile, a11y, and regression.
- [ ] Update `README.md` with all UX, component, and data changes.
- [ ] List all breaking changes and communicate if relevant.

---

# **Execution Flow (Summary Table)**

| Phase | Focus                             | Prereq? | Output                         |
| ----- | --------------------------------- | ------- | ------------------------------ |
| 1     | Audit & Docs                      | —       | Full audit, doc updates        |
| 2     | Layout, Spacing, Responsiveness   | 1       | Responsive grid, spacing fixed |
| 3     | Components, Slots, Best Practices | 2       | Reusable headers, logic split  |
| 4     | Accessibility & Feedback          | 3       | a11y, loaders, color fixes     |
| 5     | Enhanced Interactions             | 4       | Animations, icons, tooltips    |
| 6     | Code Cleanup & Reliability        | 5       | Refactored, dead code removed  |
| 7     | Visual & Cosmetic Polish          | 6       | Unified styles & icons         |
| 8     | Unpolished/Incomplete Features    | 7       | Placeholders, modal polish     |
| 9     | Testing                           | 8       | Unit/snapshot tests            |
| 10    | Final Documentation & Review      | 9       | Docs & UX review               |

---

## **How ChatGPT Should Execute:**

1. **Start with audit & docs:** Get clear baseline and reduce rework.
2. **Refactor layout/spacing:** Prevents UI bugs as features are added.
3. **Component & logic improvements:** Preps for a11y, interactivity, and tests.
4. **Accessibility, loading, error feedback:** Ensures a professional feel.
5. **Interaction polish, animation, state memory:** Boosts engagement and clarity.
6. **Final code cleanup:** Keeps codebase healthy.
7. **Cosmetic & visual tweaks:** For a crisp, modern feel.
8. **Handle incomplete features accessibly:** Shows progress.
9. **Test and review for reliability.**
10. **Deliver final docs and summary of changes.**

---

## **Key Rules:**

- Make one clear, reviewable set of changes per phase.
- Always update changelogs and tasklogs with each push.
- Never break the build between phases.
- Request explicit review before merging breaking UI/logic refactors.
- Log all steps and checklist progress in root-level logs as per braydio repo rules.

---

**Ready for ChatGPT to begin? Just say which phase or batch to start with, or specify a custom order.**
If you want this as a Markdown or tracking file for the repo, let me know!
