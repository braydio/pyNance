<template>
  <div class="refresh-controls">
    <button class="btn" @click="handleFetch" :disabled="isFetching">
      <span v-if="isFetching">Refreshing Accounts…</span>
      <span v-else>Refresh Accounts</span>
    </button>
    <button class="btn" @click="handleRefresh" :disabled="isRefreshing">
      <span v-if="isRefreshing">Refreshing Activity…</span>
      <span v-else>Refresh Account Activity</span>
    </button>
    <button class="btn" @click="syncCategories" :disabled="isSyncing">
      <span v-if="isSyncing">Syncing Categories…</span>
      <span v-else>Sync Categories</span>
    </button>
  </div>
</template>

<script>
export default {
  name: "RefreshControls",
  props: {
    onFetch: { type: Function, required: true },
    onRefresh: { type: Function, required: true },
  },
  data() {
    return {
      isFetching: false,
      isRefreshing: false,
      isSyncing: false,
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
    async syncCategories() {
      this.isSyncing = true;
      try {
        const response = await axios.post("/api/categories/refresh");
        if (response.data.status === "success") {
          alert("Categories synced from Plaid successfully.");
        } else {
          alert("Failed to sync categories: " + response.data.message);
        }
      } catch (err) {
        alert("Error syncing categories: " + err.message);
      } finally {
        this.isSyncing = false;
      }
    }
  },
};
</script>

<style scoped>
.refresh-controls {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 1rem;
}

.btn {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
  padding: 0.5rem 1.25rem;
}

.btn:hover {
  color: var(--themed-bg);
  background-color: var(--neon-mint);
}
</style>
