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
:root {
  /* Gruvbox-inspired palette for Hyprland Arch Linux */
  --background: #282828;    /* Dark Gruvbox background */
  --foreground: #ebdbb2;    /* Light Gruvbox foreground */
  --accent: #fabd2f;        /* Accent yellow */
  --error: #cc241d;         /* Error red for delete buttons */
  --border: #3c3836;        /* Subtle border color */
  --hover: #32302f;         /* Hover background color */
  --input-bg: #1d2021;      /* Slightly darker background for inputs */
}

/* Accounts Table Container */
.accounts-table {
  background-color: var(--background);
  color: var(--foreground);
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

/* Heading */
.accounts-table h2 {
  margin-top: 0;
  color: var(--accent);
  font-family: "Fira Code", monospace;
  font-size: 1.5rem;
}

/* Filter Row */
.filter-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* Filter Input */
.filter-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background-color: var(--input-bg);
  color: var(--foreground);
  font-family: "Fira Code", monospace;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s ease;
}
.filter-input:focus {
  border-color: var(--accent);
}

/* Toggle Delete Buttons Button */
.toggle-delete-btn {
  padding: 0.5rem 1rem;
  background-color: var(--accent);
  color: var(--background);
  border: 1px solid var(--accent);
  border-radius: 4px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  font-weight: bold;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.toggle-delete-btn:hover {
  background-color: var(--hover);
  transform: translateY(-1px);
}

/* Table Styling */
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  text-align: left;
  font-family: "Fira Code", monospace;
  font-size: 0.9rem;
}
th {
  cursor: pointer;
  background-color: var(--input-bg);
  color: var(--foreground);
  position: relative;
}
th span {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Delete Button Styling */
.delete-btn {
  padding: 0.4rem 0.8rem;
  background-color: var(--error);
  color: #ffffff;
  border: 1px solid var(--error);
  border-radius: 4px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  font-weight: bold;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.delete-btn:hover {
  background-color: #ff6666;
  transform: translateY(-1px);
}

/* Table Row Hover Effect */
tbody tr:hover {
  background-color: var(--hover);
}
</style>
