// frontend/eslint.config.js
// ESLint 9+ Flat Config version

import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import pluginCypress from "eslint-plugin-cypress/flat";
import prettierPlugin from "eslint-plugin-prettier";
import vueConfigPrettier from "@vue/eslint-config-prettier";

export default [
  // Base JS + Vue recommended settings
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],

  // Vue + Prettier integration (Flat Config compatible)
  {
    files: ["**/*.js", "**/*.vue", "**/*.ts", "**/*.jsx", "**/*.tsx"],
    plugins: {
      vue: pluginVue,
      cypress: pluginCypress,
      prettier: prettierPlugin,
    },
    rules: {
      // Prettier
      "prettier/prettier": "warn",

      // Vue
      "vue/multi-word-component-names": "off",

      // Cypress globals and rules
      "no-undef": "off", // Cypress uses globals like cy, describe
    },
  },

  // Cypress-specific config
  {
    files: ["cypress/e2e/**/*.{js,ts,jsx,tsx}", "cypress/support/**/*.{js,ts,jsx,tsx}"],
    ...pluginCypress.configs.recommended,
    rules: {
      "no-unused-vars": "off",
      "cypress/no-unnecessary-waiting": "warn",
    },
  },

  // Ignore certain folders
  {
    ignores: [
      "dist/**",
      "coverage/**",
      "node_modules/**",
      "*.min.js",
      "*.config.{js,cjs,mjs}",
    ],
  },

  // Vue-specific parser & language options
  {
    name: "vue-files",
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
    },
  },

  // Configuration and global files
  {
    files: ["*.config.{js,cjs,mjs}"],
    languageOptions: {
      globals: {
        module: "writable",
        require: "readonly",
        process: "readonly",
      },
    },
  },

  // Final Prettier config override (disables conflicting rules)
  vueConfigPrettier,
];
