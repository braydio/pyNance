/** @type {import('tailwindcss').Config} */
import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'
import aspectRatio from '@tailwindcss/aspect-ratio'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx,css}'],
  theme: {
    extend: {
      colors: {
        bg: {
          dark: '#1e1e1e',
          secondary: '#242424',
          sec: 'rgba(255, 255, 255, 0.1)',
        },
        text: {
          light: '#f5f5f5',
          muted: '#a1a1aa',
        },
        border: {
          secondary: '#3f3f46',
        },
        divider: 'rgba(255, 255, 255, 0.12)',
        shadow: 'rgba(0, 0, 0, 0.6)',
        neon: {
          purple: '#c084fc',
          mint: '#2fffa7',
        },
        accent: {
          yellow: '#facc15',
          purpleHover: '#d9a6fd',
          mint: '#2fffa7',
        },
        error: '#f87171',
        hover: {
          DEFAULT: 'rgba(255, 255, 255, 0.1)',
          light: 'rgba(255, 255, 255, 0.06)',
          glow: 'rgba(192, 132, 252, 0.6)',
        },
        frosted: {
          bg: 'rgba(255, 255, 255, 0.08)',
        },
        fontFamily: {
          sans: [
            'Source Code Pro',
            'ui-sans-serif',
            'Inter',
            'system-ui',
            'sans-serif',
          ],
        },
      },
    },
    plugins: [forms, typography, aspectRatio],
    darkMode: 'class',
  }
}
