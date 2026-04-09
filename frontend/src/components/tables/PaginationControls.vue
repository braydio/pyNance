<template>
  <div class="pagination-container">
    <div class="pagination-row" role="group" aria-label="Pagination controls">
      <BaseButton
        class="pagination-button"
        :disabled="currentPage <= 1"
        @click="goToFirst"
        aria-label="Go to first page"
        tone="neutral"
        variant="outline"
        radius="pill"
        size="sm"
      >
        « First
      </BaseButton>
      <BaseButton
        class="pagination-button"
        :disabled="currentPage <= 1"
        @click="goToPrev"
        aria-label="Go to previous page"
        tone="neutral"
        variant="outline"
        radius="pill"
        size="sm"
      >
        ‹ Prev
      </BaseButton>

      <div class="page-list" aria-label="Select page">
        <BaseButton
          v-if="hasLeadingGap"
          class="pagination-chip"
          @click="goToPage(1)"
          aria-label="Go to page 1"
          tone="neutral"
          variant="ghost"
          radius="pill"
          size="sm"
        >
          1
        </BaseButton>
        <span v-if="hasLeadingGap" class="gap">…</span>

        <BaseButton
          v-for="pageNumber in visiblePages"
          :key="pageNumber"
          class="pagination-chip"
          :active="pageNumber === currentPage"
          @click="goToPage(pageNumber)"
          :aria-current="pageNumber === currentPage ? 'page' : undefined"
          tone="neutral"
          variant="ghost"
          radius="pill"
          size="sm"
        >
          {{ pageNumber }}
        </BaseButton>

        <span v-if="hasTrailingGap" class="gap">…</span>
        <BaseButton
          v-if="hasTrailingGap"
          class="pagination-chip"
          @click="goToPage(totalPages)"
          tone="neutral"
          variant="ghost"
          radius="pill"
          size="sm"
        >
          {{ totalPages }}
        </BaseButton>
      </div>

      <BaseButton
        class="pagination-button"
        :disabled="currentPage >= totalPages"
        @click="goToNext"
        aria-label="Go to next page"
        tone="neutral"
        variant="outline"
        radius="pill"
        size="sm"
      >
        Next ›
      </BaseButton>
      <BaseButton
        class="pagination-button"
        :disabled="currentPage >= totalPages"
        @click="goToLast"
        aria-label="Go to last page"
        tone="neutral"
        variant="outline"
        radius="pill"
        size="sm"
      >
        Last »
      </BaseButton>
    </div>

    <div class="info-row">
      <div class="page-input">
        <label class="sr-only" for="page-entry">Jump to page</label>
        <span>Page</span>
        <BaseInput
          id="page-entry"
          type="number"
          min="1"
          :max="totalPages"
          v-model.number="editablePage"
          @enter="jumpToPage"
          class="page-field"
          size="sm"
          radius="sm"
        />
        <span>of {{ totalPages }}</span>
        <BaseButton
          class="go-button"
          tone="accent"
          variant="solid"
          radius="sm"
          size="sm"
          @click="jumpToPage"
          >Go</BaseButton
        >
      </div>
      <span v-if="rangeLabel" class="range-label">{{ rangeLabel }}</span>
    </div>
  </div>
</template>

<script>
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'

/**
 * PaginationControls
 *
 * Reusable pagination bar with first/last navigation, direct page entry, and
 * range metadata. Emits the destination page through the `change-page` event.
 */
export default {
  name: 'PaginationControls',
  components: { BaseButton, BaseInput },
  props: {
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true },
    pageSize: { type: Number, default: null },
    totalItems: { type: Number, default: 0 },
  },
  emits: ['change-page'],
  data() {
    return {
      editablePage: this.currentPage,
    }
  },
  computed: {
    visiblePages() {
      const total = Math.max(1, this.totalPages)
      const maxButtons = 5
      const half = Math.floor(maxButtons / 2)
      let start = Math.max(1, this.currentPage - half)
      let end = start + maxButtons - 1

      if (end > total) {
        end = total
        start = Math.max(1, end - maxButtons + 1)
      }

      const pages = []
      for (let i = start; i <= end; i += 1) pages.push(i)
      return pages
    },
    hasLeadingGap() {
      return this.visiblePages.length && this.visiblePages[0] > 1
    },
    hasTrailingGap() {
      return (
        this.visiblePages.length &&
        this.visiblePages[this.visiblePages.length - 1] < this.totalPages
      )
    },
    rangeLabel() {
      if (!this.pageSize || !this.totalItems) return ''
      const start = (this.currentPage - 1) * this.pageSize + 1
      const end = Math.min(this.totalItems, start + this.pageSize - 1)
      return `Showing ${start.toLocaleString()}–${end.toLocaleString()} of ${this.totalItems.toLocaleString()}`
    },
  },
  watch: {
    currentPage(val) {
      this.editablePage = val
    },
    totalPages(val) {
      if (this.editablePage > val) {
        this.editablePage = val
      }
    },
  },
  methods: {
    clampPage(page) {
      if (!page || Number.isNaN(page)) return 1
      return Math.min(Math.max(1, Math.trunc(page)), this.totalPages || 1)
    },
    goToPage(page) {
      const target = this.clampPage(page)
      this.editablePage = target
      this.$emit('change-page', target)
    },
    goToPrev() {
      if (this.currentPage > 1) this.goToPage(this.currentPage - 1)
    },
    goToNext() {
      if (this.currentPage < this.totalPages) this.goToPage(this.currentPage + 1)
    },
    goToFirst() {
      this.goToPage(1)
    },
    goToLast() {
      this.goToPage(this.totalPages)
    },
    jumpToPage() {
      this.goToPage(this.editablePage)
    },
  },
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.pagination-container {
  @apply mt-4 flex flex-col gap-3 rounded-2xl border border-subtle bg-surface-3 px-4 py-3 shadow-lg;
}

.pagination-row {
  @apply flex flex-wrap items-center justify-center gap-2 text-sm;
}

.pagination-button {
  @apply font-semibold;
}

.page-list {
  @apply flex items-center gap-1 rounded-full border border-subtle bg-surface-2 px-2 py-1 shadow-inner;
}

.pagination-chip {
  min-width: 36px;
}

.gap {
  @apply px-1 text-muted;
}

.info-row {
  @apply flex flex-col items-center justify-center gap-2 text-xs text-muted sm:flex-row sm:text-sm;
}

.page-input {
  @apply flex items-center gap-2 rounded-full border border-subtle bg-surface-2 px-3 py-2 shadow-inner;
}

.page-field {
  @apply w-16 text-center;
}

.go-button {
  @apply text-xs font-semibold;
}

.range-label {
  @apply text-muted;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
