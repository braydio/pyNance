<template>
  <aside
    class="chart-details-sidebar"
    :class="{ 'chart-details-sidebar--open': isOpen }"
    role="complementary"
    :aria-labelledby="headerId"
  >
    <button
      type="button"
      class="chart-details-sidebar__toggle gradient-toggle-btn"
      :class="{ 'is-active': isOpen }"
      :aria-expanded="isOpen.toString()"
      :aria-controls="contentId"
      @click="toggleSidebar"
    >
      <span :id="headerId" class="chart-details-sidebar__label">Details</span>
      <span class="chart-details-sidebar__icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" focusable="false" aria-hidden="true">
          <path
            d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.1l3.71-3.87a.75.75 0 0 1 1.08 1.04l-4.25 4.43a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06Z"
            fill="currentColor"
          />
        </svg>
      </span>
      <span class="sr-only">{{ isOpen ? 'Collapse chart details' : 'Expand chart details' }}</span>
    </button>
    <div
      v-show="isOpen"
      :id="contentId"
      class="chart-details-sidebar__content"
      role="region"
      :aria-labelledby="headerId"
    >
      <h3 class="chart-details-sidebar__heading">Details</h3>
      <fieldset class="chart-details-sidebar__fieldset">
        <legend class="sr-only">Chart overlay toggles</legend>
        <label>
          <input
            type="checkbox"
            :checked="show7Day"
            @change="emit('update:show7Day', $event.target.checked)"
          />
          7 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="show30Day"
            @change="emit('update:show30Day', $event.target.checked)"
          />
          30 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgIncome"
            @change="emit('update:showAvgIncome', $event.target.checked)"
          />
          Avg Income
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgExpenses"
            @change="emit('update:showAvgExpenses', $event.target.checked)"
          />
          Avg Expenses
        </label>
      </fieldset>
    </div>
  </aside>
</template>

<script setup>
/**
 * Sidebar displaying chart overlay controls with accessible toggle behavior.
 */
import { ref, toRefs } from 'vue'

const props = defineProps({
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:show7Day',
  'update:show30Day',
  'update:showAvgIncome',
  'update:showAvgExpenses',
])

const { show7Day, show30Day, showAvgIncome, showAvgExpenses } = toRefs(props)

const isOpen = ref(true)
const uniqueId = Math.random().toString(36).slice(2, 9)
const contentId = `chart-details-${uniqueId}`
const headerId = `${contentId}-header`

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}
</script>

<style scoped>
.chart-details-sidebar {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
  pointer-events: none;
}

.chart-details-sidebar__toggle {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-width: 8.5rem;
  transition: box-shadow 0.3s ease;
}

.chart-details-sidebar__toggle:focus-visible {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-cyan) 35%, transparent);
}

.chart-details-sidebar__icon {
  display: inline-flex;
  width: 1rem;
  height: 1rem;
  transition: transform 0.2s ease;
}

.chart-details-sidebar__icon svg {
  width: 100%;
  height: 100%;
}

.chart-details-sidebar--open .chart-details-sidebar__icon {
  transform: rotate(180deg);
}

.chart-details-sidebar__content {
  pointer-events: auto;
  min-width: 14rem;
  max-width: 16rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-cyan) 40%, transparent);
  background: color-mix(in srgb, var(--color-bg) 90%, var(--color-accent-cyan) 10%);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: grid;
  gap: 0.5rem;
}

.chart-details-sidebar__heading {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart-details-sidebar__fieldset {
  display: grid;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: 0;
}

.chart-details-sidebar__fieldset label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.chart-details-sidebar__fieldset input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-accent-cyan);
}
</style>
