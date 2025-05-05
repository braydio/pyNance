<template>
  <div>
    <NotificationsBar />

    <div class="p-6">
      <h1 class="text-3xl font-bold mb-4">Recurring Transactions</h1>
      <p class="text-gray-600 mb-4">Upcoming due items for your linked accounts:</p>

      <ul v-if="reminders.length" class="space-y-3">
        <li v-for="(reminder, index) in reminders" :key="index"
          class="p-4 bg-white rounded-md shadow border border-gray-200">
          {{ reminder }}
        </li>
      </ul>

      <div v-else class="text-gray-500 text-sm italic">
        No reminders due within the next 7 days.
      </div>
    </div>
  </div>
</template>

<script>
import NotificationsBar from "@/components/NotificationsBar.vue";

export default {
  name: "RecurringTx",
  components: {
    NotificationsBar,
  },
  data() {
    return {
      reminders: [],
    };
  },
  async mounted() {
    const accountId = "demo-account"; // 🔁 Replace this with dynamic user/account context
    try {
      const response = await fetch(`/api/${accountId}/recurring`);
      const json = await response.json();

      if (json.status === "success") {
        this.reminders = json.reminders;
      } else {
        console.error("Failed to fetch reminders:", json.message);
      }
    } catch (err) {
      console.error("Error fetching recurring reminders:", err);
    }
  },
};
</script>

<style scoped>
/* Optional scoped styling here */
</style>
