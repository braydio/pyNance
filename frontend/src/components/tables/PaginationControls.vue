<template>
  <div class="pagination-container">
    <div class="pagination-row" role="group" aria-label="Pagination controls">
      <button
        class="pagination-button"
        :disabled="currentPage <= 1"
        @click="goToFirst"
        aria-label="Go to first page"
      >
        « First
      </button>
      <button
        class="pagination-button"
        :disabled="currentPage <= 1"
        @click="goToPrev"
        aria-label="Go to previous page"
      >
        ‹ Prev
      </button>

      <div class="page-list" aria-label="Select page">
        <button
          v-if="hasLeadingGap"
          class="pagination-chip"
          @click="goToPage(1)"
          aria-label="Go to page 1"
        >
          1
        </button>
        <span v-if="hasLeadingGap" class="gap">…</span>

        <button
          v-for="pageNumber in visiblePages"
          :key="pageNumber"
          class="pagination-chip"
          :class="{ active: pageNumber === currentPage }"
          @click="goToPage(pageNumber)"
          :aria-current="pageNumber === currentPage ? 'page' : undefined"
        >
          {{ pageNumber }}
        </button>

        <span v-if="hasTrailingGap" class="gap">…</span>
        <button v-if="hasTrailingGap" class="pagination-chip" @click="goToPage(totalPages)">
          {{ totalPages }}
        </button>
      </div>

      <button
        class="pagination-button"
        :disabled="currentPage >= totalPages"
        @click="goToNext"
        aria-label="Go to next page"
      >
        Next ›
      </button>
      <button
        class="pagination-button"
        :disabled="currentPage >= totalPages"
        @click="goToLast"
        aria-label="Go to last page"
      >
        Last »
      </button>
    </div>

    <div class="info-row">
      <div class="page-input">
        <label class="sr-only" for="page-entry">Jump to page</label>
        <span>Page</span>
        <input
          id="page-entry"
          type="number"
          min="1"
          :max="totalPages"
          v-model.number="editablePage"
          @keyup.enter="jumpToPage"
          class="page-field"
        />
        <span>of {{ totalPages }}</span>
        <button class="go-button" @click="jumpToPage">Go</button>
      </div>
      <span v-if="rangeLabel" class="range-label">{{ rangeLabel }}</span>
    </div>
  </div>
</template>

<script>
/**
 * PaginationControls
 *
 * Reusable pagination bar with first/last navigation, direct page entry, and
 * range metadata. Emits the destination page through the `change-page` event.
 */
export default {
  name: 'PaginationControls',
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
  @apply rounded-full border border-subtle bg-surface-1 px-3 py-1.5 font-semibold text-secondary transition;
  @apply hover:border-strong hover-surface disabled:cursor-not-allowed disabled:opacity-50;
}

.page-list {
  @apply flex items-center gap-1 rounded-full border border-subtle bg-surface-2 px-2 py-1 shadow-inner;
}

.pagination-chip {
  @apply min-w-[36px] rounded-full px-3 py-1 text-sm font-semibold text-secondary transition;
  @apply hover-surface hover:text-primary;
}

.pagination-chip.active {
  @apply bg-surface-1 text-primary border border-strong shadow;
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
  @apply w-16 rounded-md border border-subtle bg-surface-1 px-2 py-1 text-center text-primary outline-none;
  @apply focus:border-strong focus:ring-1;
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--interactive-focus) 65%, transparent);
}

.go-button {
  @apply rounded-md px-3 py-1 text-xs font-semibold transition;
  background-color: var(--accent-primary);
  color: var(--accent-primary-contrast);
}

.go-button:hover {
  background-color: color-mix(in srgb, var(--accent-primary) 85%, #ffffff 15%);
}

.go-button:focus-visible {
  @apply outline-none;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--interactive-focus) 65%, transparent);
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
