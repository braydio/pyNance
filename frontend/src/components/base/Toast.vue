<!-- frontend/src/components/base/Toast.vue -->
<template>
  <div v-if="visible" :class="['toast', type]" @click="close">
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

<style scoped>
.toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  padding: 1rem;
  border-radius: 8px;
  color: white;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  z-index: 9999;
  cursor: pointer;
}
.toast.success {
  background-color: #28a745;
}
.toast.error {
  background-color: #dc3545;
}
</style>
