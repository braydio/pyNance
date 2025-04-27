<script setup>
import Navbar from "@/components/Navbar.vue"
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
    <RouterView />
  </main>
</template>

<style>
@import "@/styles/global-colors.css";
@import "@/styles/buttons.css";
@import "@/styles/typography.css";
@import "@/styles/layout.css";
@import "@/styles/utilities.css";

/* example dev banner using your “cosmic rose” or “bar-alert” palette */
.env-banner-dev {
  background: var(--dev-alert-bg);
  color: var(--dev-alert-text);
  text-align: center;
  font-weight: bold;
  padding: 0.5rem;
  border-bottom: 2px solid var(--dev-alert-border);
  /* or var(--bar-alert) */
  box-shadow: 0 2px 8px var(--shadow);
  text-transform: uppercase;
}
</style>
