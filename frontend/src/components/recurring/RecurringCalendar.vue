<template>
  <div class="max-w-[900px] mx-auto p-4">
    <h2 class="text-xl font-bold mb-4">Recurring Transaction Calendar</h2>
    <div class="grid grid-cols-7 gap-2">
      <div v-for="day in days" :key="day.date" class="p-2 border rounded-xl shadow-sm text-center">
        <div class="font-semibold">{{ day.date.getDate() }}</div>
        <div v-if="day.transactions.length">
          <div v-for="tx in day.transactions" :key="tx.id" class="text-sm text-green-600">
            {{ tx.name }} - ${{ tx.amount }}
          </div>
        </div>
        <div v-else class="text-xs text-[var(--color-text-muted)]">No events</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "RecurringCalendar",
  props: {
    recurringTransactions: {
      type: Array,
      required: true,
    },
  },
  computed: {
    days() {
      const today = new Date();
      const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
      const result = [];

      for (let i = 1; i <= daysInMonth; i++) {
        const date = new Date(today.getFullYear(), today.getMonth(), i);
        const transactions = this.recurringTransactions.filter(tx => {
          const txDay = new Date(tx.next_date).getDate();
          return txDay === i;
        });
        result.push({ date, transactions });
      }

      return result;
    },
  },
};
</script>

