<template>
  <div class="card mt-6 font-mono space-y-4">
    <h3 class="heading-md text-left">Transactions</h3>
    <div class="overflow-auto rounded-2xl border border-gray-200 shadow">
      <table class="min-w-full divide-y divide-gray-200 rounded-2xl overflow-hidden">
        <thead class="bg-gray-50">
          <tr>
            <th v-for="col in columns" :key="col.key" @click="sortTable(col.key)"
              class="px-3 py-2 text-left select-none cursor-pointer font-bold uppercase text-xs tracking-wide transition"
              :class="{
                'text-accent-green': col.key === 'amount',
                'text-accent-cyan': col.key === 'date',
                'text-accent-yellow': col.key === 'account',
                'text-accent-orange': col.key === 'description',
                'text-primary': !['amount', 'date', 'account', 'description'].includes(col.key)
              }">
              {{ col.label }}
              <span v-if="sortKey === col.key" class="ml-1 font-black text-accent-yellow">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(tx, i) in sortedTransactions" :key="tx.transaction_id" :class="[
            i % 2 === 1 ? 'bg-accent-cyan/10' : '',
            'hover:bg-accent-cyan/20 hover:shadow-sm transition'
          ]">
            <td class="px-4 py-2 text-xs text-accent-cyan font-mono">
              {{ formatDate(tx.date) || "N/A" }}
            </td>
            <td class="px-4 py-2 font-semibold whitespace-nowrap text-accent-green"
              :class="{ 'text-error': tx.amount < 0 }">
              {{ formatAmount(tx.amount) }}
            </td>
            <td class="px-4 py-2 text-xs text-accent-yellow font-bold">
              {{ formatAccount(tx) }}
            </td>
            <td class="px-4 py-2 text-xs text-accent-orange font-bold">
              {{ formatDescription(tx) }}
            </td>
            <td class="px-4 py-2 text-xs text-primary">
              {{ formatCategory(tx) }}
            </td>
          </tr>
          <tr v-if="sortedTransactions.length === 0">
            <td :colspan="columns.length" class="px-4 py-10 text-center text-muted bg-dark rounded-b-2xl">
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: "TransactionsTable",
  props: {
    transactions: {
      type: Array,
      default: () => [],
    },
    sortKey: String,
    sortOrder: Number,
    search: String
  },
  data() {
    return {
      columns: [
        { key: 'date', label: 'Date' },
        { key: 'amount', label: 'Amount' },
        { key: 'account', label: 'Account' },
        { key: 'description', label: 'Description' },
        { key: 'category', label: 'Category' }
      ]
    }
  },
  computed: {
    sortedTransactions() {
      // Sorting and filtering handled in parent; this just passes through
      return [...this.transactions]
    }
  },
  methods: {
    sortTable(key) {
      this.$emit('sort', key)
    },
    formatDate(dateStr) {
      if (!dateStr) return "N/A"
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        year: '2-digit',
        month: 'short',
        day: 'numeric'
      })
    },
    formatAmount(amount) {
      const number = parseFloat(amount)
      if (isNaN(number)) return "N/A"
      return number.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    formatAccount(tx) {
      // Account: Show institution name + account name/number, fallback if missing
      let parts = []
      if (tx.institution_name) parts.push(tx.institution_name)
      if (tx.account_name) parts.push(tx.account_name)
      return parts.length ? parts.join(" ") : "N/A"
    },
    formatDescription(tx) {
      // Merchant: Title Case & normalize ALL CAPS, Description: literary case
      const merchant = tx.merchant_name
        ? this.toTitleCase(tx.merchant_name)
        : ""
      const desc = tx.description
        ? this.literaryFormat(tx.description)
        : ""
      if (merchant && desc) return `${merchant}: ${desc}`
      if (merchant) return merchant
      if (desc) return desc
      return ""
    },
    formatCategory(tx) {
      const p = tx.primary_category || ''
      const d = tx.detailed_category || ''
      if (p && d) return `${this.capitalizeFirst(p)}: ${this.capitalizeFirst(d)}`
      if (p) return this.capitalizeFirst(p)
      if (d) return this.capitalizeFirst(d)
      return "Unknown"
    },
    capitalizeFirst(str) {
      if (!str) return ""
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
    },
    literaryFormat(str) {
      if (!str) return ""
      // Capitalize first letter after punctuation or at start of string
      return str.replace(/(^\s*\w|[.!?]\s*\w)/g, s => s.toUpperCase())
    },
    toTitleCase(str) {
      if (!str) return ""
      // Turn ALL CAPS and mixed input into "Title Case"
      // e.g. "CHASE BANK" -> "Chase Bank"
      //      "CVS/pharmacy" -> "Cvs/Pharmacy"
      //      "THE CO-OP" -> "The Co-Op"
      return str
        .toLowerCase()
        .replace(/([^\s\/-]+)(?=[\s\/-]?)/g, w =>
          w.charAt(0).toUpperCase() + w.slice(1)
        )
    }
  }
}
</script>

<style scoped>
@import "../../assets/css/main.css";
</style>
