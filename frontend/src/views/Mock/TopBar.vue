'// DashboardMock.vue — Action Item 1: Feature-Complete Top Bar <template>

  <div class="dashboard-top-bar">
    <div class="left-section">
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <span class="text-sm text-gray-500">Welcome back, Brayden</span>
    </div>

    ```
    <div class="center-section">
      <div class="date-range-selector">
        <label for="dateRange" class="mr-2 text-sm text-gray-600">Date Range:</label>
        <select v-model="selectedRange" id="dateRange" class="border rounded p-1">
          <option value="7">Last 7 Days</option>
          <option value="30">Last 30 Days</option>
          <option value="90">Last 90 Days</option>
        </select>
      </div>
    </div>

    <div class="right-section flex items-center gap-4">
      <div class="account-toggle">
        <label for="accountToggle" class="text-sm text-gray-600">Show All Accounts:</label>
        <input type="checkbox" v-model="showAllAccounts" id="accountToggle" class="ml-2">
      </div>

      <div class="profile-menu relative">
        <button @click="toggleMenu" class="flex items-center space-x-2">
          <img src="/mock-profile.jpg" alt="Profile" class="w-8 h-8 rounded-full">
          <span class="text-sm">Brayden</span>
        </button>
        <div v-if="menuOpen" class="absolute right-0 mt-2 w-40 bg-white border rounded shadow-md z-10">
          <ul class="text-sm">
            <li class="px-4 py-2 hover:bg-gray-100 cursor-pointer">Settings</li>
            <li class="px-4 py-2 hover:bg-gray-100 cursor-pointer">Logout</li>
          </ul>
        </div>
      </div>
    </div>
    ```

  </div>
</template>

<script>
export default {
  name: "DashboardTopBar",
  data() {
    return {
      selectedRange: '30',
      showAllAccounts: true,
      menuOpen: false,
    }
  },
  methods: {
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
    }
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.dashboard-top-bar {
  @apply flex justify-between items-center bg-white shadow px-6 py-4 rounded-b-md;
}

.left-section {
  @apply flex flex-col;
}

.center-section {
  @apply flex items-center;
}

.right-section {
  @apply flex items-center;
}
</style>
