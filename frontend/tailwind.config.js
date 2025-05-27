
import forms from '@tailwindcss/forms';
import typography from '@tailwindcss/typography';
import aspectRatio from '@tailwindcss/aspect-ratio';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend/index.html",
    "./frontend/src/**/*.{vue,js,ts,jsx,tsx}", // ✅ FIXED: matches actual structure
  ],
  theme: {
    extend: {
      boxShadow: {
        card: '0 2px 8px rgba(0, 0, 0, 0.1)',
      },
      borderRadius: {
        lg: '0.75rem',
      },
    },
  },
  plugins: [forms, typography, aspectRatio],
};

