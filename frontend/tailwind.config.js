/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./**/*.{html,js,ts,jsx,tsx}"
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
  plugins: [],
}

