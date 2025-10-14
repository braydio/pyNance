<template>
  <section class="space-y-6">
    <header class="space-y-1">
      <h3 class="text-lg font-semibold">Allocation targets</h3>
      <p class="text-sm text-muted">
        Distribute the planning balance across savings and goals. Keep the total under 100% to stay
        on budget.
      </p>
    </header>

    <div
      v-if="!categories.length"
      class="rounded border border-dashed border-muted p-6 text-center text-sm text-muted"
    >
      Add allocation categories to begin distributing this scenario's balance.
    </div>

    <div v-else class="space-y-5">
      <div v-for="category in categories" :key="category" class="space-y-2">
        <div class="flex items-center justify-between text-sm">
          <span class="font-medium">{{ formatCategory(category) }}</span>
          <span class="text-muted">{{ allocations[category] ?? 0 }}%</span>
        </div>
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
        <div class="flex items-center justify-between text-xs text-muted">
          <span>{{ formatCurrencyAmount(allocations[category] ?? 0) }}</span>
          <span>{{ 100 - (allocations[category] ?? 0) }}% unallocated</span>
        </div>
      </div>
    </div>

    <footer class="allocation-summary" :class="{ 'is-invalid': !isValid }">
      <div>
        <strong>{{ totalPercent }}%</strong>
        of the balance allocated
        <span class="text-muted">({{ totalCurrencyLabel }})</span>
      </div>
      <div>
        <span :class="remainingClass">{{ remainingCopy }}</span>
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
  (e: 'update:modelValue', value: Record<string, number>): void
  (
    e: 'change',
    payload: {
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
  color: var(--color-muted, #64748b);
}

.text-error {
  color: #b91c1c;
}

.text-success {
  color: #047857;
}

.border-muted {
  border-color: rgba(148, 163, 184, 0.3);
}

.allocator-slider {
  width: 100%;
}

.allocation-summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background-color: rgba(15, 118, 110, 0.04);
}

.allocation-summary.is-invalid {
  background-color: rgba(239, 68, 68, 0.08);
}
</style>
