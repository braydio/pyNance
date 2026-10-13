<template>
  <header class="page-header">
    <div class="page-header__identity">
      <component v-if="icon" :is="icon" class="page-header__icon" aria-hidden="true" />
      <div class="min-w-0">
        <h1 class="page-header__title">
          <slot name="title" />
        </h1>
        <p v-if="$slots.subtitle" class="page-header__subtitle">
          <slot name="subtitle" />
        </p>
      </div>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
/**
 * PageHeader
 * Unboxed page identity header for views with an icon adjacent to the title and optional actions slot.
 *
 * Props:
 * - icon: optional icon component rendered beside the title
 *
 * Slots:
 * - title: main heading text
 * - subtitle: supporting description text
 * - actions: optional right-aligned action controls
 */
defineProps({
  icon: {
    type: [String, Object, Function],
    default: null,
  },
})
</script>

<style scoped>
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  padding: 0.25rem 0 1rem;
}

.page-header__identity {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}

.page-header__icon {
  width: 1.25rem;
  height: 1.25rem;
  flex: none;
  color: var(--color-text-muted);
}

.page-header__title {
  font-size: 1.5rem;
  line-height: 1.2;
  font-weight: 700;
}

.page-header__subtitle {
  margin-top: 0.15rem;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
</style>
