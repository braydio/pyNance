<script setup>
/**
 * Root application shell.
 * Renders the navigation bar and centers all routed views.
 */
import Navbar from "@/components/layout/Navbar.vue"
import { RouterView } from "vue-router"

// use Vite’s built-in env variable:
const isDev = import.meta.env.VITE_SESSION_MODE === "development"
</script>

<template>
  <header>
    <!-- If in dev mode, show a bright banner -->
    <div v-if="isDev" class="env-banner-dev">
      This is a development build. This is not a production build. Check your .env
    </div>
    <Navbar />
  </header>

  <main>
    <div class="container">
      <RouterView />
    </div>
  </main>
</template>
