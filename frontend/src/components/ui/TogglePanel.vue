<template>
  <div class="toggle-panel">
    <button
      type="button"
      :aria-expanded="modelValue ? 'true' : 'false'"
      :aria-controls="panelId"
      :class="[
        'toggle-header flex items-center justify-between w-full p-3 text-left rounded-t-lg',
        modelValue ? 'toggle-header--open' : '',
      ]"
      @click="toggle"
    >
      <div class="flex items-center gap-2">
        <component v-if="icon" :is="icon" class="w-4 h-4" aria-hidden="true" />
        <span :class="['font-medium', dense ? 'text-sm' : 'text-base']">{{ title }}</span>
      </div>
      <div class="flex items-center gap-2">
        <slot name="header-extra" />
        <ChevronDown
          :class="['w-4 h-4 transition-transform', modelValue ? 'rotate-180' : '']"
          aria-hidden="true"
        />
      </div>
    </button>

    <transition name="slide-down">
      <div
        v-if="modelValue"
        :id="panelId"
        :class="['panel-content border-x border-b rounded-b-lg', dense ? 'p-2' : 'p-4']"
      >
        <slot />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { useId } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  modelValue: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: [String, Object],
    default: null,
  },
  dense: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const panelId = `toggle-panel-${useId()}`

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>

<style scoped>
/* Surfaces and borders come from the active theme (data-theme), not a .dark class. */
.toggle-panel {
  border: 1px solid var(--border-subtle);
  border-radius: 0.5rem;
  color: var(--text-primary);
  /* Allow content like dropdowns to escape bounds when needed */
  overflow: visible;
}

.toggle-header {
  background-color: var(--surface-2);
  color: var(--text-primary);
  transition: background-color 0.15s ease;
}

.toggle-header:hover,
.toggle-header--open {
  background-color: var(--interactive-hover);
}

.toggle-header:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.panel-content {
  border-color: var(--border-subtle);
  background-color: var(--surface-1);
  /* Ensure nested controls are not clipped */
  overflow: visible;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: opacity 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .slide-down-enter-active,
  .slide-down-leave-active,
  .toggle-header {
    transition: none;
  }
}
</style>
