<template>
  <div>
    <div
      v-for="category in categories"
      :key="category"
      class="mb-4"
    >
      <label class="block mb-1">{{ category }}</label>
      <input
        type="range"
        min="0"
        max="100"
        :value="allocations[category]"
        @input="(e) => updateAllocation(category, Number(e.target.value))"
        class="w-full"
      />
      <span class="text-sm">{{ allocations[category] }}%</span>
    </div>
    <p>Total: {{ total }}%</p>
    <p v-if="error" class="text-error">{{ error }}</p>
  </div>
</template>

<script setup>
/**
 * Allocator component.
 *
 * Provides range inputs for assigning percentage allocations to categories
 * and validates that the total does not exceed 100%.
 *
 * v-model:
 * - `modelValue` - object mapping category names to percentage allocations.
 *
 * Props:
 * - `categories` - array of category names to allocate for.
 *
 * Emits:
 * - `update:modelValue` - emitted whenever allocations change.
 */
import { reactive, computed, watch } from 'vue'

/** Component props. */
const props = defineProps({
  categories: { type: Array, required: true },
  modelValue: { type: Object, default: () => ({}) },
})

/** Emit update event for v-model. */
const emit = defineEmits(['update:modelValue'])

/**
 * Internal reactive copy of allocations to track slider changes.
 * Keys correspond to category names and values are percentages.
 */
const allocations = reactive({ ...props.modelValue })

// Ensure all provided categories exist in the allocation map.
props.categories.forEach((cat) => {
  if (allocations[cat] === undefined) allocations[cat] = 0
})

/** Sync local state when parent modelValue changes. */
watch(
  () => props.modelValue,
  (val) => {
    Object.keys(allocations).forEach((k) => delete allocations[k])
    Object.assign(allocations, val)
  },
  { deep: true }
)

/** Watch local allocations and sync with parent via v-model. */
watch(
  allocations,
  (val) => emit('update:modelValue', { ...val }),
  { deep: true }
)

/** Total allocation percentage across all categories. */
const total = computed(() =>
  Object.values(allocations).reduce((sum, val) => sum + Number(val || 0), 0)
)

/** Error message shown when total exceeds 100%. */
const error = computed(() =>
  total.value > 100 ? 'Total allocation cannot exceed 100%.' : ''
)

/**
 * Update allocation for a specific category.
 *
 * @param {string} category - Category name being updated.
 * @param {number} value - New allocation percentage.
 * @returns {void}
 */
function updateAllocation(category, value) {
  allocations[category] = value
}
</script>

<style scoped>
/* Basic styling placeholder for Allocator */
</style>

