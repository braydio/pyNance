<template>
  <aside
    class="chart-details-sidebar"
    :class="{ 'chart-details-sidebar--open': isOpen }"
    role="complementary"
    :aria-labelledby="headerId"
    ref="sidebarRef"
  >
    <button
      type="button"
      class="chart-details-sidebar__toggle"
      :aria-expanded="isOpen.toString()"
      :aria-controls="contentId"
      @click="toggleSidebar"
    >
      <span :id="headerId" class="chart-details-sidebar__label">Overlays</span>
      <span class="chart-details-sidebar__icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" focusable="false" aria-hidden="true">
          <path
            d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.1l3.71-3.87a.75.75 0 0 1 1.08 1.04l-4.25 4.43a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06Z"
            fill="currentColor"
          />
        </svg>
      </span>
      <span class="sr-only">{{
        isOpen ? 'Collapse overlay options' : 'Expand overlay options'
      }}</span>
    </button>
    <div
      v-show="isOpen"
      :id="contentId"
      class="chart-details-sidebar__content"
      role="region"
      :aria-labelledby="headerId"
    >
      <button
        type="button"
        class="chart-details-sidebar__close"
        aria-label="Close overlay options"
        @click="closeSidebar"
      >
        &times;
      </button>
      <h3 class="chart-details-sidebar__heading">Overlay Options</h3>
      <p class="chart-details-sidebar__description">
        Toggle additional metrics directly on the chart.
      </p>
      <fieldset class="chart-details-sidebar__fieldset">
        <legend class="sr-only">Chart overlay toggles</legend>
        <label>
          <input
            type="checkbox"
            :checked="show7Day"
            @change="onOptionChange('update:show7Day', $event.target.checked)"
          />
          7 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="show30Day"
            @change="onOptionChange('update:show30Day', $event.target.checked)"
          />
          30 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgIncome"
            @change="onOptionChange('update:showAvgIncome', $event.target.checked)"
          />
          Avg Income
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgExpenses"
            @change="onOptionChange('update:showAvgExpenses', $event.target.checked)"
          />
          Avg Expenses
        </label>
        <label class="chart-details-sidebar__comparison-toggle">
          <input
            type="checkbox"
            :checked="showComparisonOverlay"
            @change="onOptionChange('update:showComparisonOverlay', $event.target.checked)"
          />
          Comparison Overlay
        </label>
      </fieldset>
    </div>
  </aside>
</template>

<script setup>
/**
 * Sidebar displaying chart overlay controls with accessible toggle behavior.
 *
 * Loads in a collapsed state and automatically collapses again whenever the user
 * selects an option or clicks outside the sidebar.
 */
import { ref, toRefs, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:show7Day',
  'update:show30Day',
  'update:showAvgIncome',
  'update:showAvgExpenses',
  'update:showComparisonOverlay',
])

const { show7Day, show30Day, showAvgIncome, showAvgExpenses, showComparisonOverlay } = toRefs(props)

const isOpen = ref(false)
const sidebarRef = ref(null)
const uniqueId = Math.random().toString(36).slice(2, 9)
const contentId = `chart-details-${uniqueId}`
const headerId = `${contentId}-header`

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}

const closeSidebar = () => {
  isOpen.value = false
}

const onOptionChange = (eventName, checked) => {
  emit(eventName, checked)
}

const handleDocumentClick = (event) => {
  if (!isOpen.value) return
  const sidebarEl = sidebarRef.value
  if (!sidebarEl) return
  if (!sidebarEl.contains(event.target)) {
    closeSidebar()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
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

.chart-details-sidebar--inline {
  position: relative;
  align-items: center;
  pointer-events: auto;
  top: auto;
  right: auto;
}

.chart-details-sidebar__toggle {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0.65rem;
  border-radius: 0.35rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-yellow) 75%, transparent);
  background: color-mix(in srgb, var(--color-bg-dark) 70%, var(--color-accent-yellow) 30%);
  color: var(--color-text-light);
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

.chart-details-sidebar--inline .chart-details-sidebar__toggle {
  font-size: 0.7rem;
  padding: 0.2rem 0.55rem;
}

.chart-details-sidebar__toggle:hover,
.chart-details-sidebar__toggle:focus-visible {
  background: color-mix(in srgb, var(--color-bg-dark) 45%, var(--color-accent-yellow) 55%);
  color: var(--color-text-light);
  outline: none;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-yellow) 30%, transparent);
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
  min-width: 12rem;
  max-width: 14rem;
  padding: 0.6rem;
  border-radius: 0.35rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-yellow) 70%, transparent);
  background: linear-gradient(
    140deg,
    color-mix(in srgb, var(--color-bg-dark) 78%, var(--color-accent-yellow) 22%),
    color-mix(in srgb, var(--color-bg-sec) 70%, var(--color-accent-green) 30%)
  );
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.35);
  display: grid;
  gap: 0.55rem;
  position: relative;
}

.chart-details-sidebar--inline .chart-details-sidebar__content {
  position: absolute;
  top: calc(100% + 0.45rem);
  left: 50%;
  right: auto;
  transform: translateX(-50%);
  z-index: 20;
}

.chart-details-sidebar__heading {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart-details-sidebar__description {
  margin: 0;
  font-size: 0.72rem;
  color: color-mix(in srgb, var(--color-text-light) 75%, transparent);
}

.chart-details-sidebar__close {
  position: absolute;
  top: 0.35rem;
  right: 0.35rem;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 0.2rem;
  border: 0.5px solid color-mix(in srgb, var(--color-accent-yellow) 45%, transparent);
  color: color-mix(in srgb, var(--color-text-light) 75%, transparent);
  background: color-mix(in srgb, var(--color-bg-dark) 65%, transparent);
  font-size: 1rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.chart-details-sidebar__close:hover,
.chart-details-sidebar__close:focus-visible {
  color: var(--color-text-light);
  background: color-mix(in srgb, var(--color-accent-yellow) 22%, transparent);
  box-shadow: 0 0 10px color-mix(in srgb, var(--color-accent-yellow) 50%, transparent);
  outline: none;
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
  font-size: 0.78rem;
  color: var(--color-text-light);
}

.chart-details-sidebar__fieldset input[type='checkbox'] {
  width: 0.9rem;
  height: 0.9rem;
  accent-color: var(--color-accent-cyan);
}

.chart-details-sidebar__comparison-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
</style>
