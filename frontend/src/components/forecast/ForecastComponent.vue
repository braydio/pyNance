<template>
  <div class="forecast-view p-6 space-y-6">

    <!-- Header -->
    <header class="text-center">
      <h1 class="text-3xl font-bold">Financial Forecast</h1>
      <p class="text-gray-500">Simulate your future net delta and balance shifts</p>
    </header>

    <!-- Top Grid: Summary + Chart -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

      <!-- Summary Panel -->
      <div class="bg-white rounded-2xl shadow p-4">
        <h2 class="text-xl font-semibold mb-2">Summary</h2>
        <p>Current Balance: $4,300.00</p>
        <p>Forecasted Net Delta: +$450.00</p>
        <p>Projected Balance: $4,750.00</p>

        <div class="mt-4 space-y-2">
          <label class="block text-sm font-medium">Manual Recurring Income ($)</label>
          <input type="number" class="w-full border p-2 rounded" placeholder="e.g. 200" />

          <label class="block text-sm font-medium mt-4">Liability Rate (%)</label>
          <input type="number" class="w-full border p-2 rounded" placeholder="e.g. 2.1" />
        </div>
      </div>

      <!-- Forecast Chart Placeholder -->
      <div class="bg-white rounded-2xl shadow p-4 h-64 flex items-center justify-center text-gray-400">
        <span>[Chart will go here]</span>
      </div>
    </div>

    <!-- Forecast Breakdown -->
    <div class="bg-white rounded-2xl shadow p-4">
      <h2 class="text-xl font-semibold mb-4">Forecast Breakdown</h2>
      <ul class="space-y-1">
        <li>+ Salary: $2,500</li>
        <li>- Rent: $1,200</li>
        <li>- Subscriptions: $200</li>
        <li>+ Investment Returns: $300</li>
        <li>- Liability Deductions: $90</li>
        <li>+ Manual Recurring: $200</li>
      </ul>
    </div>

    <!-- Custom Adjustments Form -->
    <div class="bg-white rounded-2xl shadow p-4">
      <h2 class="text-xl font-semibold mb-4">Custom Adjustments</h2>
      <form class="space-y-4">
        <div>
          <label class="block text-sm font-medium">Type</label>
          <select class="w-full border p-2 rounded">
            <option>Income</option>
            <option>Expense</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium">Amount ($)</label>
          <input type="number" class="w-full border p-2 rounded" />
        </div>
        <div>
          <label class="block text-sm font-medium">Frequency</label>
          <select class="w-full border p-2 rounded">
            <option>Weekly</option>
            <option>Biweekly</option>
            <option>Monthly</option>
            <option>One-Time</option>
          </select>
        </div>
        <button type="button" class="mt-2 px-4 py-2 bg-blue-500 text-white rounded">Add</button>
      </form>
    </div>

  </div>
</template>

<script>
export default {
  name: "Forecast",
};
</script>

<style scoped>
.forecast-view {
  background: #f9fafb;
  min-height: 100vh;
}
</style>
