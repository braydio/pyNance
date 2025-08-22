<template>
  <div class="toggle-panel">
    <button
      @click="toggle"
      :class="[
        'toggle-header flex items-center justify-between w-full p-3 text-left rounded-t-lg',
        'hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors',
        modelValue ? 'bg-gray-50 dark:bg-gray-800' : 'bg-gray-100 dark:bg-gray-900'
      ]"
    >
      <div class="flex items-center gap-2">
        <component v-if="icon" :is="icon" class="w-4 h-4" />
        <span :class="['font-medium', dense ? 'text-sm' : 'text-base']">{{ title }}</span>
      </div>
      <div class="flex items-center gap-2">
        <slot name="header-extra" />
        <ChevronDown 
          :class="['w-4 h-4 transition-transform', modelValue ? 'rotate-180' : '']" 
        />
      </div>
    </button>
    
    <transition name="slide-down">
      <div v-if="modelValue" :class="['panel-content border-x border-b rounded-b-lg', dense ? 'p-2' : 'p-4']">
        <slot />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  modelValue: {
    type: Boolean,
    default: false
  },
  icon: {
    type: [String, Object],
    default: null
  },
  dense: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>

<style scoped>
.toggle-panel {
  border: 1px solid rgb(229, 231, 235);
  border-radius: 0.5rem;
  overflow: hidden;
}

.dark .toggle-panel {
  border-color: rgb(55, 65, 81);
}

.toggle-header:focus {
  outline: 2px solid rgb(59, 130, 246);
  outline-offset: 2px;
}

.panel-content {
  border-color: inherit;
  background-color: var(--color-bg-primary, white);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease-in-out;
  transform-origin: top;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: scaleY(0);
}

.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  transform: scaleY(1);
}
</style>
