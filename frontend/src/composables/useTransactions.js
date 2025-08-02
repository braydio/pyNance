// File: src/composables/useTransactions.js

/**
 * Provides transaction table state and helpers for dashboard components.
 * Handles pagination, search, and sort logic while fetching from the API.
 */
import { ref, computed, onMounted } from "vue";
import { fetchTransactions as fetchTransactionsApi } from "@/api/transactions";

export function useTransactions(pageSize = 15) {
  const transactions = ref([]);
  const searchQuery = ref("");
  const sortKey = ref(null);
  const sortOrder = ref(1);
  const currentPage = ref(1);
  const totalPages = ref(1);

  /**
   * Fetch a page of transactions from the API.
   *
   * Some backend responses omit the `status` field and return the data
   * object directly. This helper normalizes both shapes so the table renders
   * even when the backend does not include a status key.
   */
  const fetchTransactions = async () => {
    try {
      const res = await fetchTransactionsApi({
        page: currentPage.value,
        page_size: pageSize,
      });

      // No need to check for 'data' property
      if (!res || typeof res !== 'object' || !('transactions' in res)) {
        console.error('Unexpected response shape:', res);
        alert('Received an unexpected response from the server.');
        return;
      }

      transactions.value = res.transactions || [];
      const total = res.total != null ? res.total : 0;
      totalPages.value = Math.max(1, Math.ceil(total / pageSize));
    } catch (error) {
      console.error("Error fetching transactions:", error);
    }
  };


  const changePage = (delta) => {
    currentPage.value = Math.max(1, Math.min(currentPage.value + delta, totalPages.value));
    fetchTransactions();
  };

  const setSort = (key) => {
    if (sortKey.value === key) {
      sortOrder.value *= -1;
    } else {
      sortKey.value = key;
      sortOrder.value = 1;
    }
  };

  const filteredTransactions = computed(() => {
    let filtered = transactions.value.filter((tx) =>
      Object.values(tx).some((val) =>
        val && val.toString().toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    );
    if (sortKey.value) {
      filtered.sort((a, b) => {
        let valA = a[sortKey.value] || "";
        let valB = b[sortKey.value] || "";
        return valA.toString().localeCompare(valB.toString()) * sortOrder.value;
      });
    }
    return filtered;
  });

  onMounted(fetchTransactions);

  return {
    transactions,
    searchQuery,
    sortKey,
    sortOrder,
    currentPage,
    totalPages,
    fetchTransactions,
    changePage,
    setSort,
    filteredTransactions,
  };
}

