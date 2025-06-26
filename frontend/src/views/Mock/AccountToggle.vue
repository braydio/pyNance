<template>
  <div class="flex justify-between items-center p-4 shadow-md bg-white rounded-b-2xl">
    <!-- Left: Greeting + Date Selector -->
    <div class="flex flex-col gap-1">
      <h1 class="text-xl font-semibold text-gray-800">Welcome back, Brayden 👋</h1>
      <div class="flex items-center gap-2">
        <label for="daterange" class="text-sm text-gray-600">Date Range:</label>
        <select id="daterange" class="border rounded px-2 py-1 text-sm text-gray-700">
          <option>Last 7 Days</option>
          <option>Last 30 Days</option>
          <option>This Month</option>
          <option>Custom...</option>
        </select>
      </div>
    </div>

    ```
    <!-- Right: Account Toggle + Profile -->
    <div class="flex items-center gap-4">
      <!-- Account Visibility Toggle -->
      <div class="flex gap-2 items-center">
        <span class="text-sm text-gray-600">Accounts:</span>
        <button class="bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs px-2 py-1 rounded"
          @click="toggleAccount('Checking')">
          Checking
        </button>
        <button class="bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs px-2 py-1 rounded"
          @click="toggleAccount('Savings')">
          Savings
        </button>
      </div>

      <!-- Mock Profile Dropdown -->
      <div class="relative">
        <button class="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">
          <img src="https://via.placeholder.com/32" class="w-6 h-6 rounded-full" alt="Profile" />
          <span class="text-sm text-gray-700">Brayden</span>
        </button>
      </div>
    </div>
    ```

  </div>
</template>

<script setup>
const toggleAccount = (account) => {
  console.log("Toggled visibility for:", account);
  // implement actual logic later
};
</script>

<style scoped>
@reference "../../assets/css/main.css";
select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}
</style>
