// frontend/eslint.config.js

import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import pluginCypress from "eslint-plugin-cypress/flat";
import tsParser from "@typescript-eslint/parser";

export default [
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],

  {
    files: ["**/*.{js,vue,ts,jsx,tsx}"],
    plugins: {
      vue: pluginVue,
      cypress: pluginCypress,
    },
    rules: {
      "vue/multi-word-component-names": "off",
      "no-undef": "off",
      "no-unused-vars": ["error", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
      }],
    },
  },

  {
    files: [
      "cypress/e2e/**/*.{js,ts,jsx,tsx}",
      "cypress/support/**/*.{js,ts,jsx,tsx}",
    ],
    ...pluginCypress.configs.recommended,
    rules: {
      "no-unused-vars": "off",
      "cypress/no-unnecessary-waiting": "warn",
    },
  },

  {
    ignores: [
      "dist/**",
      "coverage/**",
      "node_modules/**",
      "*.min.js",
      "*.config.{js,cjs,mjs}",
    ],
  },

  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
        parser: {
          js: tsParser,
          ts: tsParser,
        },
      },
    },
  },

  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
  },

  {
    files: ["**/*.{jsx,tsx}"],
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
  },

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
];
