<template>
  <div class="ledger">
    <div :class="['ledger-scroll', { 'ledger-scroll--sticky': stickyHeader }]">
      <table class="ledger-table">
        <caption
          v-if="caption"
          :class="['ledger-caption', { 'ledger-caption--sr': captionHidden }]"
        >
          {{
            caption
          }}
        </caption>
        <slot />
      </table>
    </div>
  </div>
</template>

<script setup>
/**
 * Shared ledger table shell: a single containing surface with one horizontal scroll owner.
 * Styling lives in the `.ledger-*` classes in assets/css/main.css.
 */
defineProps({
  caption: { type: String, default: '' },
  captionHidden: { type: Boolean, default: true },
  stickyHeader: { type: Boolean, default: false },
})
</script>
