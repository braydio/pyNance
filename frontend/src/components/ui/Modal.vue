<template>
  <!-- Shared dialog: teleported to <body>, labelled, focus-trapped, scroll-locked. -->
  <Teleport to="body">
    <transition name="modal-pop" appear>
      <div class="modal-backdrop" data-testid="modal-backdrop" @click.self="emitClose">
        <div
          ref="dialogRef"
          class="modal-dialog card glass shadow-2xl rounded-xl"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          tabindex="-1"
          :style="{ '--modal-max-width': maxWidth }"
        >
          <button type="button" class="modal-close" aria-label="Close dialog" @click="emitClose">
            <span aria-hidden="true" class="text-xl">&times;</span>
          </button>

          <div :id="titleId" class="modal-title text-xl font-semibold">
            <slot name="title" />
          </div>

          <div class="modal-body">
            <slot name="body" />
          </div>

          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, useId } from 'vue'
import { useModalA11y } from '@/composables/useModalA11y'

const props = defineProps({
  /** Determines the max-width size (e.g. 'sm', 'md', 'lg', 'xl', '2xl', '3xl'). */
  size: { type: String, default: '2xl' },
})

const emit = defineEmits(['close'])

const dialogRef = ref(null)
const titleId = `modal-title-${useId()}`

/** Close the modal and emit event to parent. */
function emitClose() {
  emit('close')
}

useModalA11y({
  dialogRef,
  onEscape: () => {
    emitClose()
    return true
  },
})

const sizeMap = {
  sm: '24rem',
  md: '28rem',
  lg: '32rem',
  xl: '36rem',
  '2xl': '42rem',
  '3xl': '48rem',
}

const maxWidth = computed(() => sizeMap[props.size] || sizeMap['2xl'])
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.45);
}

.modal-dialog {
  position: relative;
  display: flex;
  flex-direction: column;
  width: min(100%, var(--modal-max-width, 42rem));
  max-height: calc(100dvh - 2rem);
  padding: 1.25rem;
  color: var(--text-primary);
}

.modal-title {
  padding-right: 2.5rem;
  margin-bottom: 1rem;
}

.modal-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.modal-footer {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.modal-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.25rem;
  min-height: 2.25rem;
  border-radius: 0.5rem;
  color: var(--text-secondary);
}

.modal-close:hover {
  color: var(--text-primary);
  background: var(--interactive-hover);
}

.modal-close:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.modal-pop-enter-active,
.modal-pop-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.modal-pop-enter-from,
.modal-pop-leave-to {
  opacity: 0;
  transform: scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .modal-pop-enter-active,
  .modal-pop-leave-active {
    transition: none;
  }
}
</style>
