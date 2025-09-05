<template>
  <div class="space-y-4" data-testid="transactions-actions-sidebar">
    <ImportFileSelector />
    <div>
      <input
        v-model="query"
        type="text"
        placeholder="Search transactions..."
        class="input w-full"
      />
    </div>
    <UiButton variant="outline" class="w-full" @click="$emit('open-scanner')">
      Open Scanner
    </UiButton>
  </div>
</template>

<script setup>
/**
 * AccountActionsSidebar (transactions variant)
 * Sidebar providing file import, search filter and scanner access for
 * the Transactions view.
 *
 * Emits:
 * - `update:modelValue` when search query changes
 * - `open-scanner` when the scanner button is clicked
 */
import { computed } from 'vue'
import ImportFileSelector from '@/components/forms/ImportFileSelector.vue'
import UiButton from '@/components/ui/Button.vue'

const props = defineProps({
  /** Current search query */
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'open-scanner'])

const query = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})
</script>
