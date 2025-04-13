// File: src/composables/useTransactions.js

import { ref, computed, onMounted } from "vue";
import axios from "axios";

export function useTransactions(pageSize = 15) {
  const transactions = ref([]);
  const searchQuery = ref("");
  const sortKey = ref(null);
  const sortOrder = ref(1);
  const currentPage = ref(1);
  const totalPages = ref(1);

  const fetchTransactions = async () => {
    try {
      // Updated to read from res.data.data
      const res = await axios.get(
        `/api/transactions/get_transactions?page=${currentPage.value}&page_size=${pageSize}`
      );
      if (res.data.status === "success") {
        // Change: access transactions and total from the nested data object
        transactions.value = res.data.data.transactions;
        totalPages.value = Math.ceil(res.data.data.total / pageSize);
      }
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

