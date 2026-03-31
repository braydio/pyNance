<template>
  <fieldset class="section-container scope-group">
    <legend class="text-sm font-semibold">Choose what data to share</legend>
    <div class="scope-options" role="group" aria-label="Choose what data to share">
      <button
        v-for="product in availableProducts"
        :key="product.id"
        type="button"
        @click="toggle(product.id)"
        :aria-pressed="modelValue.includes(product.id)"
        class="scope-card"
        :class="{ 'is-selected': modelValue.includes(product.id) }"
      >
        <span class="scope-card__header">
          <span class="text-sm font-semibold">{{ product.label }}</span>
          <span v-if="modelValue.includes(product.id)" class="scope-card__selected-pill"
            >Selected</span
          >
        </span>
        <span class="text-xs text-muted">{{ product.helper }}</span>
      </button>
    </div>
  </fieldset>
</template>

<script setup>
const availableProducts = [
  {
    id: 'transactions',
    label: 'Transactions',
    helper: 'Enables account balances and transaction history for cash flow insights.',
  },
  {
    id: 'investments',
    label: 'Investments',
    helper: 'Enables holdings and investment activity tracking in your portfolio views.',
  },
  {
    id: 'liabilities',
    label: 'Liabilities',
    helper: 'Enables loan and credit detail tracking for debt monitoring.',
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
.scope-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
  border: 0;
  padding: 0;
}

.scope-group > legend {
  padding: 0;
}

.scope-options {
  display: grid;
  gap: 0.75rem;
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
    transform 0.2s ease,
    background-color 0.2s ease;
}

.scope-card:hover {
  border-color: var(--color-accent-purple);
}

.scope-card.is-selected {
  border-color: color-mix(in srgb, var(--color-accent-cyan) 45%, var(--color-accent-purple));
  background: color-mix(in srgb, var(--color-accent-cyan) 18%, var(--color-bg));
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--color-accent-cyan) 65%, transparent),
    0 10px 24px rgba(0, 0, 0, 0.16);
  transform: translateY(-1px);
}

.scope-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.scope-card__selected-pill {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--color-bg-dark);
  background: color-mix(in srgb, var(--color-accent-cyan) 80%, white 20%);
  border-radius: 999px;
  padding: 0.12rem 0.4rem;
}
</style>
