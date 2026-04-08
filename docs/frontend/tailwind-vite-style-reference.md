# Styling Architecture Reference: Tailwind CSS + Vite & PostCSS Integration

_Last updated: 2026-04-08_

## Overview

This document provides a detailed reference for how styling is configured in the `braydio/pyNance` frontend as of May 2025. It covers the rationale, tool choices, configuration details, limitations, and performance advantages related to our current setup.

## Styling Tools & Libraries

### ✅ **Tailwind CSS**

**Why:** Utility-first CSS framework offering a fast, consistent way to build modern UIs without custom CSS bloat.

**How it's used:**

- Defined via global stylesheet (`app.css`) that includes `@tailwind base`, `@tailwind components`, and `@tailwind utilities`.
- Extended via Tailwind config for theming and design tokens.

**Advantages:**

- Consistency across components
- Rapid prototyping with utility classes
- Easily themeable and extensible

### ✅ **@tailwindcss/postcss Plugin**

**Why:** This project relies on the official PostCSS plugin so we can keep using `postcss.config.cjs` for Autoprefixer and any additional PostCSS transforms.

**Installation:**

```bash
npm install -D @tailwindcss/postcss
```

**Configured in `postcss.config.cjs`:**

```js
module.exports = {
  plugins: {
    "@tailwindcss/postcss": {},
    autoprefixer: {},
  },
};
```

**Why not `@tailwindcss/vite`:**

- Keeping PostCSS allows compatibility with existing tooling and custom processing steps.

## Framework Context

- The frontend is built with **Vue 3**.
- We use **ES module** syntax across the project (`type: "module"` in `package.json`).

This has implications:

- No `module.exports` allowed — all config files must use `export default`.
- If CommonJS is absolutely needed, `.cjs` extensions must be used.

## Styling in SFCs (Single File Components)

### Using Tailwind with `<style>` Blocks

#### Option 1: `@reference` global styles

```vue
<style>
@reference "../../app.css";
.my-class {
  @apply text-red-500 font-bold;
}
</style>
```

> 📌 `@reference` makes global utility classes available to CSS blocks without duplicating them in the bundle.

#### Option 2: CSS Variables (Preferred for Performance)

```vue
<style>
.my-class {
  color: var(--tw-text-red-500);
}
</style>
```

> ⚠️ Avoid `@apply` in isolated stylesheets if you don’t need dynamic utility composition. CSS variables are faster.

## Semantic Theme Tokens

`frontend/src/styles/theme.css` defines semantic tokens that should be used for all neutral surfaces, borders, and text hierarchy:

- Surface layers: `--surface-1`, `--surface-2`, `--surface-3`
- Borders: `--border-subtle`, `--border-strong`
- Text hierarchy: `--text-primary`, `--text-secondary`, `--text-muted`
- Interactive states: `--interactive-hover`, `--interactive-focus`, `--interactive-pressed`

These are exposed through utility classes in `frontend/src/assets/css/main.css` such as:

- `bg-surface-1`, `bg-surface-2`, `bg-surface-3`
- `border-subtle`, `border-strong`
- `text-primary`, `text-secondary`, `text-muted`
- `hover-surface`, `pressed-surface`, `focus-ring`

## Rule: No Hardcoded Neutrals

Do not use hardcoded neutral palettes in Vue templates or scoped styles (for example `bg-gray-*`, `text-gray-*`, `border-slate-*`, `bg-neutral-*`).

### Vue template example

```vue
<section class="ui-card p-4">
  <h3 class="text-primary">Snapshot selection</h3>
  <p class="text-secondary">Use semantic tokens for neutral text.</p>
  <button class="ui-control hover-surface focus-ring">Refresh</button>
</section>
```

### Scoped style example

```vue
<style scoped>
@reference "../../assets/css/main.css";

.table-shell {
  @apply border border-subtle bg-surface-2;
}

.table-row:hover {
  @apply hover-surface;
}
</style>
```

## Known Limitations

- `@apply` **does not inherit theme customizations** in module-scoped or component-local style blocks unless `@reference` is used.
- Global styles must be referenced manually for scoped styles to access utility classes.
- Tailwind plugin requires **Vite 4+** to function optimally.

## Deprecated

- `vite.config.js` — redundant if `vite.config.ts` is present and should be removed.

## Action Log Summary

- 🟢 PostCSS configuration retained for Autoprefixer support.
- 🟡 Tailwind Vite plugin not enabled.
- ✅ Styling conventions aligned with Tailwind 4 best practices.
- 📄 This document added as a styling reference.

---

For further development, use this document as a guide for maintaining consistency in how Tailwind is used across Vue components and CSS entry points.
