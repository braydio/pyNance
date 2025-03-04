<template>
  <div class="controls">
    <button @click="handleFetch" :disabled="isFetching">
      <span v-if="isFetching">Refreshing Accounts…</span>
      <span v-else>Refresh Accounts</span>
    </button>
    <button @click="handleRefresh" :disabled="isRefreshing">
      <span v-if="isRefreshing">Refreshing Activity…</span>
      <span v-else>Refresh Account Activity</span>
    </button>
  </div>
</template>

<script>
export default {
  name: "RefreshControls",
  props: {
    onFetch: {
      type: Function,
      required: true,
    },
    onRefresh: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      isFetching: false,
      isRefreshing: false,
    };
  },
  methods: {
    async handleFetch() {
      this.isFetching = true;
      try {
        await this.onFetch();
      } catch (err) {
        console.error("Error in fetch:", err);
      } finally {
        this.isFetching = false;
      }
    },
    async handleRefresh() {
      this.isRefreshing = true;
      try {
        await this.onRefresh();
      } catch (err) {
        console.error("Error in refresh:", err);
      } finally {
        this.isRefreshing = false;
      }
    },
  },
};
</script>

<style scoped>
.controls {
  display: flex;
  gap: 0.5rem;
}
.controls button {
  background-color: var(--gruvbox-accent);
  color: var(--gruvbox-fg);
  border: 1px solid var(--gruvbox-accent);
  padding: 0.5rem 1rem;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s, color 0.2s, border 0.2s;
}
.controls button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.controls button:hover:not(:disabled) {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-accent);
  border: 1px solid var(--gruvbox-accent);
}
</style>
