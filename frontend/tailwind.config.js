/** @type {import('tailwindcss').Config} */
import defaultTheme from 'tailwindcss/defaultTheme'
import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'
import aspectRatio from '@tailwindcss/aspect-ratio'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx,css}'],
  theme: {
    extend: {
      colors: {
        'bg-dark': '#1e1e1e',
        'bg-secondary': '#242424',
        'bg-sec': 'rgba(255, 255, 255, 0.1)',
        'text-primary': '#f5f5f5',
        'text-muted': '#a1a1aa',
        'border-secondary': '#3f3f46',
        divider: 'rgba(255, 255, 255, 0.12)',
        shadow: 'rgba(0, 0, 0, 0.6)',
        accent: {
          yellow: '#dbc074',
          purple: '#9d79d6',
          cyan: '#63cdcf',
          blue: '#719cd6',
          red: '#c94f6d',
          green: '#81b29a',
          orange: '#f4a261',
          magenta: '#d67ad2',
        },
        error: '#f87171',
        hover: {
          DEFAULT: 'rgba(255, 255, 255, 0.1)',
          light: 'rgba(255, 255, 255, 0.06)',
          glow: 'rgba(192, 132, 252, 0.6)',
        },
        'frosted-bg': 'rgba(255, 255, 255, 0.08)',
      },
      fontFamily: {
        sans: [
          'Source Code Pro',
          'ui-sans-serif',
          'Inter',
          'system-ui',
          'sans-serif',
          ...defaultTheme.fontFamily.sans,
        ],
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            color: theme('colors.text-primary'),
            a: {
              color: theme('colors.accent.purple'),
              '&:hover': {
                color: theme('colors.accent.cyan'),
              },
            },
            h1: { color: theme('colors.text-primary') },
            h2: { color: theme('colors.text-primary') },
            h3: { color: theme('colors.text-primary') },
            strong: { color: theme('colors.text-primary') },
            code: { color: theme('colors.accent.yellow') },
          },
        },
      }),
    },
  },
  plugins: [forms, typography, aspectRatio],
}
