// tailwind.config.js
import forms from '@tailwindcss/forms';
import typography from '@tailwindcss/typography';
import aspectRatio from '@tailwindcss/aspect-ratio';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'page-bg': 'var(--page-bg)',
        'theme-fg': 'var(--theme-fg)',
        'surface': 'var(--surface)',
        'divider': 'var(--divider)',
        'input-bg': 'var(--input-bg)',
      },
    },
  },
  plugins: [forms, typography, aspectRatio],
};

