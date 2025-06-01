<template>
  <div class="p-6 space-y-6">
    <!-- App Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">pyNance Dashboard</h1>
      <button
        @click="refreshData"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
      >
        Refresh
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Net Worth</p>
        <p class="text-xl font-semibold text-green-600">$24,893.22</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">YTD Spending</p>
        <p class="text-xl font-semibold text-red-500">$9,340.12</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Total Accounts</p>
        <p class="text-xl font-semibold text-gray-800">6</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Upcoming Bills</p>
        <p class="text-xl font-semibold text-yellow-600">$1,203.55</p>
      </div>
    </div>
  </div>
</template>

<script setup>
function refreshData() {
  // placeholder – swap this for actual refresh logic
  console.log("Refreshing data...");
}
</script>