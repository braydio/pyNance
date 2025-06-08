<template>
  <transition name="modal-fade">
    <div v-if="true" class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black bg-opacity-50 p-4" @click.self="emitClose">
      <div class="card glass max-w-2xl w-full relative mt-20 shadow-2xl">
        <!-- Close button -->
        <button class="absolute top-2 right-2 text-gray-500 hover:text-black" @click="emitClose">
          <span class="text-xl">&times;</span>
        </button>

        <!-- Modal Title -->
        <div class="text-xl font-semibold mb-4">
          <slot name="title" />
        </div>

        <!-- Modal Body -->
        <div class="max-h-[70vh] overflow-y-auto">
          <slot name="body" />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
const emit = defineEmits(['close']);
function emitClose() {
  emit('close');
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
