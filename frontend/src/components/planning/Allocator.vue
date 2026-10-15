<template>
  <section class="space-y-6">
    <header class="space-y-1">
      <h3 class="text-lg font-semibold">Where remaining money is assigned</h3>
      <p class="text-sm text-muted">
        Split your planning balance across savings and goals. The total can't go over 100%.
      </p>
    </header>

    <div
      v-if="!categories.length"
      class="rounded border border-dashed border-muted p-6 text-center text-sm text-muted"
    >
      Add allocation categories to begin distributing this scenario's balance.
    </div>

    <div v-else class="space-y-5">
      <div
        v-for="category in categories"
        :key="category"
        class="allocator-row"
        :data-testid="`allocator-row-${category}`"
      >
        <span class="allocator-row__name font-medium">{{ formatCategory(category) }}</span>
        <input
          :aria-label="`Allocation for ${formatCategory(category)}`"
          :max="100"
          :min="0"
          :value="allocations[category] ?? 0"
          class="allocator-slider"
          step="1"
          type="range"
          @input="onSliderInput(category, $event)"
        />
        <label class="allocator-row__percent">
          <span class="sr-only">Percent for {{ formatCategory(category) }}</span>
          <input
            :max="100"
            :min="0"
            :value="allocations[category] ?? 0"
            class="input allocator-number"
            inputmode="numeric"
            step="1"
            type="number"
            :data-testid="`allocator-number-${category}`"
            @input="onSliderInput(category, $event)"
          />
          <span aria-hidden="true">%</span>
        </label>
        <span class="allocator-row__amount">{{
          formatCurrencyAmount(allocations[category] ?? 0)
        }}</span>
      </div>
    </div>

    <footer
      class="allocation-summary"
      :class="{ 'is-invalid': !isValid }"
      role="status"
      aria-live="polite"
      data-testid="allocation-summary"
    >
      <div>
        <strong>{{ totalPercent }}%</strong>
        of the balance allocated
        <span class="text-muted">({{ totalCurrencyLabel }})</span>
      </div>
      <div>
        <span :class="remainingClass">{{ remainingCopy }}</span>
        <span class="text-muted"> · {{ remainingCurrencyLabel }} unassigned</span>
      </div>
    </footer>

    <p v-if="!isValid" class="text-sm text-error">
      Allocation exceeds 100%. Lower one or more sliders to continue.
    </p>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { formatCurrency } from '@/utils/currency'
import { clampAllocations, sanitizePercent } from '@/utils/planning'

const props = withDefaults(
  defineProps<{
    categories: string[]
    modelValue: Record<string, number>
    currencyCode?: string
    availableCents?: number
  }>(),
  {
    categories: () => [],
    modelValue: () => ({}),
    currencyCode: 'USD',
    availableCents: 0,
  },
)

const emit = defineEmits<{
  (_e: 'update:modelValue', _value: Record<string, number>): void
  (
    _e: 'change',
    _payload: {
      allocations: Record<string, number>
      totalPercent: number
      remainingPercent: number
      totalCents: number
      isValid: boolean
    },
  ): void
}>()

const allocations = reactive<Record<string, number>>({})

watch(
  () => props.categories,
  (categories) => {
    const known = new Set(categories)
    Object.keys(allocations).forEach((key) => {
      if (!known.has(key)) delete allocations[key]
    })
    categories.forEach((category) => {
      if (allocations[category] == null) allocations[category] = props.modelValue[category] ?? 0
    })
  },
  { immediate: true },
)

watch(
  () => props.modelValue,
  (model) => {
    Object.entries(model).forEach(([key, value]) => {
      allocations[key] = sanitizePercent(value)
    })
  },
  { deep: true, immediate: true },
)

watch(
  allocations,
  (value) => {
    const snapshot = { ...value }
    emit('update:modelValue', snapshot)
    emit('change', {
      allocations: snapshot,
      totalPercent: totalPercent.value,
      remainingPercent: remainingPercent.value,
      totalCents: totalAllocatedCents.value,
      isValid: isValid.value,
    })
  },
  { deep: true },
)

const totalPercent = computed(() =>
  Object.values(allocations).reduce((sum, amount) => sum + sanitizePercent(amount), 0),
)

const totalAllocatedCents = computed(() =>
  Math.round((props.availableCents * totalPercent.value) / 100),
)
const remainingPercent = computed(() => Math.max(0, 100 - totalPercent.value))
const isValid = computed(() => totalPercent.value <= 100)
const remainingCopy = computed(() => `${remainingPercent.value}% remaining`)
const remainingClass = computed(() => (isValid.value ? 'text-success' : 'text-error'))
const totalCurrencyLabel = computed(() =>
  formatCurrency(totalAllocatedCents.value / 100, props.currencyCode),
)
const remainingCurrencyLabel = computed(() =>
  formatCurrency(
    Math.max(props.availableCents - totalAllocatedCents.value, 0) / 100,
    props.currencyCode,
  ),
)

function onSliderInput(category: string, event: Event) {
  const target = event.target as HTMLInputElement
  const value = Number.parseFloat(target.value)
  const { next } = clampAllocations(allocations, category, value)
  Object.entries(next).forEach(([key, amount]) => {
    allocations[key] = amount
  })
}

function formatCategory(category: string) {
  return category.replace(/[:_]/g, ' › ')
}

function formatCurrencyAmount(percent: number) {
  const cents = Math.round((props.availableCents * sanitizePercent(percent)) / 100)
  return formatCurrency(cents / 100, props.currencyCode)
}
</script>

<style scoped>
.text-muted {
  color: var(--text-muted);
}

.text-error {
  color: var(--text-negative);
}

.text-success {
  color: var(--text-positive);
}

.border-muted {
  border-color: var(--border-subtle);
}

.allocator-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas:
    'name amount'
    'slider percent';
  align-items: center;
  gap: 0.5rem 0.75rem;
}

.allocator-row__name {
  grid-area: name;
  overflow-wrap: anywhere;
}

.allocator-row__amount {
  grid-area: amount;
  text-align: right;
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
}

.allocator-slider {
  grid-area: slider;
  width: 100%;
  min-width: 0;
  min-height: var(--control-height-sm);
}

.allocator-row__percent {
  grid-area: percent;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.allocator-number {
  width: 4.5rem;
  min-width: 0;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

@media (min-width: 640px) {
  .allocator-row {
    grid-template-columns: minmax(8rem, 1.2fr) minmax(6rem, 2fr) auto minmax(5.5rem, auto);
    grid-template-areas: 'name slider percent amount';
  }
}

.allocation-summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-subtle);
  background-color: var(--surface-2);
  font-variant-numeric: tabular-nums;
}

.allocation-summary.is-invalid {
  border-color: var(--text-negative);
  background-color: color-mix(in srgb, var(--text-negative) 10%, var(--surface-2));
}
</style>
