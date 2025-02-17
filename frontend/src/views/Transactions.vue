<template>
  <div class="transactions-page">
    <header>
      <div>
        <h1>Transactions</h1>
        <h3>and more transactions</h3>
      </div>
      <nav class="menu">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/teller-dot">Teller.IO</router-link>
        <router-link to="/accounts">Accounts</router-link>
        <router-link to="/transactions">Transactions</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </header>
    <main>
      <div class="controls">
        <!-- (Additional controls and filters can be added here) -->
      </div>
      <div class="transactions">
        <h3>Transactions</h3>
        <table id="transactions-table" class="display">
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Name</th>
              <th>Category</th>
              <th>Merchant</th>
              <th>Account</th>
              <th>Institution</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <div id="pagination-controls">
        <button id="prevPage" @click="changePage(-1)">Previous</button>
        <span id="pageIndicator">Page {{ currentPage }} of {{ totalPages }}</span>
        <button id="nextPage" @click="changePage(1)">Next</button>
      </div>
    </main>
  </div>
</template>

<script>
import { onMounted, ref } from "vue";
import axios from "axios";
// Optionally, if plan to use a native Vue DataTable component,
// import it here instead of using jQuery DataTables.

export default {
  name: "Transactions",
  setup() {
    const allTransactions = ref([]);
    const currentPage = ref(1);
    const pageSize = 15;
    const totalPages = ref(1);

    const fetchTransactions = async () => {
      try {
        const res = await axios.get(`/get_transactions?page=${currentPage.value}&page_size=${pageSize}`);
        if (res.data.status === "success") {
          allTransactions.value = res.data.data.transactions;
          totalPages.value = Math.ceil(res.data.data.total / pageSize);
          renderDataTable();
        }
      } catch (error) {
        console.error("Error fetching transactions:", error);
      }
    };

    const renderDataTable = () => {
      // Here we assume jQuery DataTables is available globally.
      // If you prefer a Vue-native solution, replace this with a Vue table component.
      $("#transactions-table").DataTable({
        data: allTransactions.value,
        destroy: true,
        columns: [
          { data: "date", defaultContent: "N/A" },
          { data: "amount", defaultContent: "N/A" },
          { data: "name", defaultContent: "N/A" },
          {
            data: "category",
            render: (data) =>
              Array.isArray(data) ? data.join(", ") : data || "Uncategorized",
          },
          { data: "merchant_name", defaultContent: "Unknown" },
          { data: "account_name", defaultContent: "Unknown Account" },
          { data: "institution_name", defaultContent: "Unknown Institution" },
        ],
        pageLength: pageSize,
        ordering: true,
        searching: false,
        lengthChange: false,
        dom: '<"top"iB><"clear">rt<"bottom"p><"clear">',
        buttons: ["csv", "excel"],
        language: {
          emptyTable:
            "No transactions available. Please filter or add new transactions.",
        },
        infoCallback: function (settings, start, end, max, total) {
          return `${start} - ${end} of ${allTransactions.value.length}`;
        },
      });
    };

    const changePage = (delta) => {
      currentPage.value += delta;
      if (currentPage.value < 1) currentPage.value = 1;
      fetchTransactions();
    };

    onMounted(() => {
      fetchTransactions();
    });

    return {
      currentPage,
      totalPages,
      changePage,
    };
  },
};
</script>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f2f2f2;
}
nav.menu {
  display: flex;
  gap: 10px;
}
.transactions {
  margin-top: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
table th,
table td {
  padding: 8px;
  border: 1px solid #ddd;
}
#pagination-controls {
  margin-top: 10px;
  text-align: center;
}
</style>
