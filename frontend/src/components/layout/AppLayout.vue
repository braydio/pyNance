<template>
  <div class="min-h-screen flex flex-col">
    <header class="glass border-b" style="border-color: var(--divider); box-shadow: 0 2px 4px var(--shadow);">
      <div class="container py-6">
        <slot name="header" />
      </div>
    </header>
    <main class="flex-1 container py-6">
      <slot />
    </main>
    <footer class="glass border-t" style="border-color: var(--divider);">
      <div class="container py-4 text-center text-gray-600 text-sm">
        <slot name="footer" />
      </div>
    </footer>
  </div>
</template>

<script setup>
// Layout wrapper, no additional logic
</script>