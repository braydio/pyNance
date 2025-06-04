<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click.self="emitClose">
    <div class="bg-white rounded-2xl shadow-xl max-w-xl w-full p-6 relative">
      <!-- Close button -->
      <button class="absolute top-2 right-2 text-gray-500 hover:text-black" @click="emitClose">
        <span class="text-xl">&times;</span>
      </button>

      <!-- Modal Title -->
      <div class="text-xl font-semibold mb-4">
        <slot name="title" />
      </div>

      <!-- Modal Body -->
      <div class="max-h-[60vh] overflow-y-auto">
        <slot name="body" />
      </div>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['close']);
function emitClose() {
  emit('close');
}
</script>
