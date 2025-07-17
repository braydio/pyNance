<template>
  <div class="flex items-center justify-center gap-3 mt-4">
    <button
      class="rounded-2xl px-4 py-1 shadow text-lg bg-gray-100 border border-gray-300 text-gray-700 transition hover:bg-accent-cyan hover:text-white focus:ring-2 focus:ring-cyan-500"
      :disabled="currentPage <= 1" @click="goToPrev">
      Previous
    </button>
    <span class="flex items-center gap-1 text-sm">
      Page
      <input type="number" min="1" :max="totalPages" v-model.number="editablePage" @keyup.enter="jumpToPage"
        class="w-14 mx-1 text-center border border-gray-300 rounded px-1 py-0.5 focus:ring-2 focus:ring-accent-cyan outline-none" />
      of <span class="font-bold">{{ totalPages }}</span>
    </span>
    <button
      class="rounded-2xl px-4 py-1 shadow text-lg bg-gray-100 border border-gray-300 text-gray-700 transition hover:bg-accent-cyan hover:text-white focus:ring-2 focus:ring-cyan-500"
      :disabled="currentPage >= totalPages" @click="goToNext">
      Next
    </button>
  </div>
</template>

<script>
export default {
  name: "PaginationControls",
  props: {
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true }
  },
  data() {
    return {
      editablePage: this.currentPage
    }
  },
  watch: {
    currentPage(val) {
      this.editablePage = val
    }
  },
  methods: {
    goToPrev() {
      if (this.currentPage > 1) this.$emit('change-page', this.currentPage - 1)
    },
    goToNext() {
      if (this.currentPage < this.totalPages) this.$emit('change-page', this.currentPage + 1)
    },
    jumpToPage() {
      let page = this.editablePage
      if (!page || page < 1) page = 1
      if (page > this.totalPages) page = this.totalPages
      this.$emit('change-page', page)
    }
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.relative {
  background: var(--theme-bg);
  border-radius: 1rem;
  box-shadow: 0 1px 8px 0 rgb(30 41 59 / 10%);
}
</style>
