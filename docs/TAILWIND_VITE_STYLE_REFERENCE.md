# Styling Architecture Reference: Tailwind CSS + Vite Integration

_Last updated: 2025-05-30_

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

### ✅ **@tailwindcss/vite Plugin**

**Why:** Official Tailwind plugin for Vite. Replaces legacy `postcss.config.js` for better performance and developer experience.

**Installation:**

```bash
npm install -D @tailwindcss/vite
```

**Configured in `vite.config.ts`:**

```ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
});
```

**Why not PostCSS:**

- Tailwind no longer requires `postcss.config.js` when using this plugin.
- Simplifies the toolchain and reduces plugin runtime.

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
@reference "../assets/css/main.css";    /* if used inside /src/views */
@reference "../../assets/css/main.css"; /* if used inside /src/components */
.my-class {
  @apply text-red-500 font-bold;
}
</style>
```

> 📌 `@reference` makes global utility classes available to CSS blocks without duplicating them in the bundle. Views live directly under `/src`, while components are one directory deeper, requiring an extra `../` in the path.

#### Option 2: CSS Variables (Preferred for Performance)

```vue
<style>
.my-class {
  color: var(--tw-text-red-500);
}
</style>
```

> ⚠️ Avoid `@apply` in isolated stylesheets if you don’t need dynamic utility composition. CSS variables are faster.

## Known Limitations

- `@apply` **does not inherit theme customizations** in module-scoped or component-local style blocks unless `@reference` is used.
- Global styles must be referenced manually for scoped styles to access utility classes.
- Tailwind plugin requires **Vite 4+** to function optimally.

## Deprecated

- `postcss.config.js` — no longer used.
- `vite.config.js` — redundant if `vite.config.ts` is present and should be removed.

## Action Log Summary

- 🟢 PostCSS configuration confirmed absent — no need to migrate or clean up.
- 🟢 Tailwind Vite plugin is in place.
- ✅ Styling conventions aligned with Tailwind 4 best practices.
- 📄 This document added as a styling reference.

---

For further development, use this document as a guide for maintaining consistency in how Tailwind is used across Vue components and CSS entry points.
