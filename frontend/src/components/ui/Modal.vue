<template>
  <!-- Simple modal container used throughout the app -->
  <transition name="modal-pop">
    <div v-if="true" class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black bg-opacity-30 p-4" @click.self="emitClose">
      <div :class="['card glass w-auto relative mt-20 shadow-2xl rounded-xl', widthClass]">
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
import { computed } from 'vue'
const props = defineProps({
  /** Determines the max-width size (e.g. 'sm', 'md', 'lg', 'xl', '2xl'). */
  size: { type: String, default: '2xl' }
})

const emit = defineEmits(['close'])

/** Close the modal and emit event to parent. */
function emitClose() {
  emit('close')
}

const sizeMap = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '3xl': 'max-w-3xl'
}

const widthClass = computed(() => sizeMap[props.size] || 'max-w-2xl')
</script>

<style scoped>
@reference "../../assets/css/main.css";
/* width variants for Tailwind: max-w-sm max-w-md max-w-lg max-w-xl max-w-2xl max-w-3xl */
.modal-pop-enter-active,
.modal-pop-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.modal-pop-enter-from,
.modal-pop-leave-to {
  opacity: 0;
  transform: scale(0.8);
}
</style>
