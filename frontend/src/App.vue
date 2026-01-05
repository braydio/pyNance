<script setup>
/**
 * Root application shell.
 * Renders the navigation bar inside the shared AppLayout and delegates
 * page-specific spacing to routed components.
 */
import Navbar from '@/components/layout/Navbar.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { RouterView } from 'vue-router'

// use Vite’s built-in env variable:
const isDev = import.meta.env.VITE_SESSION_MODE === 'development'
</script>

<template>
  <RouterView v-slot="{ Component }">
    <AppLayout>
      <template #header>
        <!-- If in dev mode, show a bright banner -->
        <div v-if="isDev" class="env-banner-dev">
          This is a development build. This is not a production build. Check your .env
        </div>
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <Navbar />
        </div>
      </template>

      <component :is="Component" />

      <template #footer>
        <AppFooter />
      </template>
    </AppLayout>
  </RouterView>
</template>
