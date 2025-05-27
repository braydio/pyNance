<template>
  <div class="section-container mb-4">
    <h3 class="text-lg font-semibold mb-2">Select Plaid Products</h3>
    <div class="flex gap-2 flex-wrap">
      <button
        v-for="product in availableProducts"
        :key="product"
        @click="toggle(product)"
        :class="[
          'btn btn-pill transition-all duration-200',
          modelValue.includes(product)
            ? 'bg-primary text-white shadow'
            : 'btn-outline text-muted'
        ]"
      >
        {{ capitalize(product) }}
      </button>
    </div>
  </div>
</template>

<script setup>
const availableProducts = ['transactions', 'investments', 'liabilities'];

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
});
const emit = defineEmits(['update:modelValue']);

function toggle(product) {
  const next = props.modelValue.includes(product)
    ? props.modelValue.filter(p => p !== product)
    : [...props.modelValue, product];

  emit('update:modelValue', next);
}

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}
</script>

<style scoped>
.btn {
  @apply px-3 py-1 rounded-lg border text-sm cursor-pointer;
}

.btn-outline {
  @apply border-gray-400 bg-white hover:bg-gray-100;
}

.btn-pill {
  @apply rounded-full;
}

.bg-primary {
  @apply bg-blue-600;
}

.text-muted {
  @apply text-gray-600;
}
</style>
