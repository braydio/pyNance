<template>
  <div class="dashboard-footer-nav" data-testid="app-footer">
    <RouterLink class="dashboard-footer-link" to="/settings">Settings</RouterLink>
    <a class="dashboard-footer-link" href="/docs" target="_blank" rel="noopener">Docs</a>
    <a class="dashboard-footer-link" href="/support" target="_blank" rel="noopener">Support</a>
    <span class="dashboard-footer-version">v{{ appVersion }}</span>
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
