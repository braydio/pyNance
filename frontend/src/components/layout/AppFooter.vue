<template>
  <div class="flex justify-center gap-4 text-sm text-gray-600" data-testid="app-footer">
    <RouterLink to="/settings">Settings</RouterLink>
    <a href="/docs" target="_blank" rel="noopener">Docs</a>
    <a href="/support" target="_blank" rel="noopener">Support</a>
    <span>v{{ appVersion }}</span>
  </div>
</template>

<script setup>
/**
 * AppFooter
 * Reusable footer displaying navigation links and the app version.
 */
import { RouterLink } from 'vue-router'
import pkg from '../../../package.json' with { type: 'json' }

const appVersion = pkg.version
</script>

<style scoped>
/* No additional styling */
</style>
