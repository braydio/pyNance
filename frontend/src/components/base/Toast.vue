<!-- frontend/src/components/base/Toast.vue -->
<template>
  <div v-if="visible" @click="close" :class="[
    'fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg cursor-pointer text-white',
    type === 'success' ? 'bg-green-500' : 'bg-red-500'
  ]">
    {{ message }}
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  type: { type: String, default: 'success' }, // 'success' | 'error'
  message: { type: String, required: true }
})

const emit = defineEmits(['close'])

const visible = ref(true)

watch(() => props.message, () => {
  visible.value = true
  setTimeout(() => {
    visible.value = false
    emit('close')
  }, 3000)
})

function close() {
  visible.value = false
  emit('close')
}
</script>
