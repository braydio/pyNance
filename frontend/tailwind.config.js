/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx,css}'],
  theme: {
    extend: {
      colors: {
        'bg-dark': '#1e1e1e',
        'bg-secondary': '#242424',
        'neon-purple': '#c084fc',
        'neon-mint': '#2fffa7',
      },
      fontFamily: {
        sans: [
          'Source Code Pro',
          'ui-sans-serif',
          'system-ui',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}
