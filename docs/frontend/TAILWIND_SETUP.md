# Tailwind Setup Guide for pyNance Frontend (Vite + Tailwind CSS v4)

> **Last Updated:** 2025-05-25

This is the canonical reference for integrating and maintaining Tailwind CSS in the pyNance frontend project.

---

## ✅ Required File Structure

### CSS Entry File

Create or edit:

```
frontend/src/assets/tailwind.css
```

Contents:

```css
@import "tailwindcss/preflight";
@import "tailwindcss/utilities";
```

> **Note**: `@tailwind base`, `@tailwind components`, and `@tailwind utilities` are deprecated in Tailwind v4+. Use `@import` instead.

### Main Entry Import (e.g., `main.js` or `main.ts`)

```js
import "@/assets/tailwind.css";
```

---

## ✅ Tailwind Config

`frontend/tailwind.config.js`

```js
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

> Remove legacy `purge` and `mode` fields.

---

## 🔌 Optional Plugins

If you want to use forms/typography/aspect-ratio:

Install:

```bash
npm install -D @tailwindcss/forms @tailwindcss/typography @tailwindcss/aspect-ratio
```

Add to config:

```js
import forms from "@tailwindcss/forms";
import typography from "@tailwindcss/typography";
import aspectRatio from "@tailwindcss/aspect-ratio";

export default {
  content: ["./src/**/*.{vue,js,ts}"],
  plugins: [forms, typography, aspectRatio],
};
```

---

## 🧹 Common Errors

### `Cannot apply unknown utility class`

This usually means Tailwind's CSS is not loading correctly.

- ✅ Make sure you're importing the CSS file (`tailwind.css`) in `main.js`
- ✅ Make sure your class names are not dynamically generated in unsupported ways (e.g., `:class="'p-' + size"`)

---

## 🚨 Notes

- Avoid using `filters` in Vue 3; these are deprecated.
- Do not use `@tailwind` directives; use `@import` as per v4 conventions.
- When referencing shared utility classes in component `<style>` blocks use
  `@reference "../assets/css/main.css"` instead of `@import` to avoid
  duplicating styles.

---

Tag: `FRONTEND_STYLE_SETUP`
