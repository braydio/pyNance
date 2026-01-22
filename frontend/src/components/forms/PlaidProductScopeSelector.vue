<template>
  <div class="section-container mb-4">
    <h3 class="text-sm font-semibold mb-3">Choose data to share</h3>
    <div class="grid gap-3">
      <button
        v-for="product in availableProducts"
        :key="product.id"
        type="button"
        @click="toggle(product.id)"
        :aria-pressed="modelValue.includes(product.id)"
        class="scope-card"
        :class="{ 'is-selected': modelValue.includes(product.id) }"
      >
        <span class="text-sm font-semibold">{{ product.label }}</span>
        <span class="text-xs text-muted">{{ product.helper }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
const availableProducts = [
  {
    id: 'transactions',
    label: 'Transactions',
    helper: 'Share account balances and transaction history for cash flow insights.',
  },
  {
    id: 'investments',
    label: 'Investments',
    helper: 'Share holdings and investment activity to track performance.',
  },
  {
    id: 'liabilities',
    label: 'Liabilities',
    helper: 'Share loan and credit details to monitor debts.',
  },
]

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['update:modelValue'])

/**
 * Toggle a Plaid product selection in the model.
 *
 * @param {string} product - Plaid product identifier.
 */
function toggle(product) {
  const next = props.modelValue.includes(product)
    ? props.modelValue.filter((selectedProduct) => selectedProduct !== product)
    : [...props.modelValue, product]

  emit('update:modelValue', next)
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.text-muted {
  color: var(--color-text-muted);
}
.scope-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  width: 100%;
  text-align: left;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
  border: 1px solid var(--divider);
  background: var(--color-bg);
  color: var(--color-text-light);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.scope-card:hover {
  border-color: var(--color-accent-purple);
}

.scope-card.is-selected {
  border-color: var(--color-accent-purple);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
  transform: translateY(-1px);
}
</style>
