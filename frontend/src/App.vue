<script setup>

import Navbar from './components/Navbar.vue';
import { RouterView } from 'vue-router';
</script>

<template>
  <header>
    <Navbar />
  </header>
    <main>
      <RouterView />
    </main>
  </template>

<style scoped>
@import '@/styles/global-colors.css';

main {
  padding: 20px;
}

body {
  background-color: var(--themed-bg)
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

</style>

