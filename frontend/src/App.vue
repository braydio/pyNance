<script setup>
import Navbar from './components/Navbar.vue';
import { RouterView } from 'vue-router';
</script>

<template>
  <header>
    <Navbar />
  </header>
    <header class="dev-building">THIS IS A DEVELOPMENT BUILD. DEV MODE = WHAT DO YOU THINK.</header>
    <main>
      <RouterView />
    </main>
  </template>

<style scoped>
@import '@/styles/global-colors.css';

main {
  padding: 20px;
}

.dev-building {
  background-color: red;
  color: white;
  text-align: center;
}

</style>
