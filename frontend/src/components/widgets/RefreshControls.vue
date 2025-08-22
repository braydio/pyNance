<template>
  <div class="refresh-controls">
    <button class="btn-accent" @click="$emit('refresh')">
      Refresh Balances
    </button>
    <button class="btn-accent" @click="$emit('sync')">
      Sync Transactions
    </button>
  </div>
</template>

<script>
export default {
  name: "RefreshControls",
};
</script>

<style scoped>
@reference "../../assets/css/main.css";
.refresh-controls {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.btn-accent {
  background-color: transparent;
  color: var(--color-accent-purple);
  border: 1px solid var(--color-accent-purple);
  border-radius: 2rem;
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.btn-accent:hover {
  background-color: var(--color-accent-purple);
  color: var(--color-bg-dark);
}
</style>
