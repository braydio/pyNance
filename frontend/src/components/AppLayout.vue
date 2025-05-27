<template>
  <div class="min-h-screen flex flex-col bg-gray-50 text-gray-800">
    <header class="bg-white border-b border-gray-200 shadow-card">
      <div class="container py-6">
        <slot name="header" />
      </div>
    </header>
    <main class="flex-1 container py-6">
      <slot />
    </main>
    <footer class="bg-white border-t border-gray-200">
      <div class="container py-4 text-center text-gray-600 text-sm">
        <slot name="footer" />
      </div>
    </footer>
  </div>
</template>

<script setup>
// Layout wrapper, no additional logic
</script>