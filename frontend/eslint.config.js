import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import pluginCypress from 'eslint-plugin-cypress/flat'
import prettierPlugin from 'eslint-plugin-prettier'
import vueConfigPrettier from '@vue/eslint-config-prettier'

export default [
  // Base JS & Vue recommendations
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  // Integrate Prettier (stylistic lint)
  {
    plugins: { prettier: prettierPlugin },
    rules: {
      'prettier/prettier': 'warn', // Show style warnings but don’t fail build
    },
  },

  // Cypress test configuration
  {
    files: ['cypress/e2e/**/*.{js,ts,jsx,tsx}', 'cypress/support/**/*.{js,ts,jsx,tsx}'],
    ...pluginCypress.configs.recommended,
    rules: {
      'no-undef': 'off', // Cypress globals like `cy` and `describe`
    },
  },

  // Ignore non-source files
  {
    name: 'ignore-build-artifacts',
    ignores: [
      'dist/**',
      'coverage/**',
      'node_modules/**',
      '*.min.js',
    ],
  },

  // Vue-specific options
  {
    name: 'vue-files',
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
    },
  },

  // Config / globals
  {
    files: ['*.config.{js,cjs,mjs}'],
    languageOptions: {
      globals: {
        module: 'writable',
        require: 'readonly',
        process: 'readonly',
      },
    },
  },

  // Prettier final override (disable conflicting rules)
  vueConfigPrettier,
]