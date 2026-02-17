// frontend/eslint.config.js

import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import pluginCypress from "eslint-plugin-cypress/flat";
import prettierPlugin from "eslint-plugin-prettier";

export default [
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],

  {
    files: ["**/*.{js,vue,ts,jsx,tsx}"],
    plugins: {
      vue: pluginVue,
      cypress: pluginCypress,
      prettier: prettierPlugin,
    },
    rules: {
      "prettier/prettier": "warn",
      "vue/multi-word-component-names": "off",
      "no-undef": "off",
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
