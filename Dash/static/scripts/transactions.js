let allTransactions = []; // Holds all transactions
let filteredTransactions = []; // Holds filtered transactions
let currentPage = 1;
const pageSize = 15; // 15 items per page

//----------------------------------------------------
// Initialize Transactions Table on Page Load
//----------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
    await initTransactionsTable();
    setupCategoryFilterMenu();
});

//----------------------------------------------------
// Helper Function to Fetch Data
//----------------------------------------------------
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    const jsonData = await response.json();
    
    console.log(`Fetched data from ${url}:`, jsonData); // ✅ Debugging log
    return jsonData;
  } catch (error) {
    console.error(`Error fetching data from ${url}:`, error);
    throw error;
  }
}

//----------------------------------------------------
// Fetch and Render Transactions Table
//----------------------------------------------------
async function initTransactionsTable() {
  const transactionsTable = document.querySelector("#transactions-table");
  if (!transactionsTable) return;

  try {
    const { status, data } = await fetchData(`/get_transactions`);
    
    if (status === "success" && data.transactions.length > 0) {
      allTransactions = data.transactions;
      filteredTransactions = [...allTransactions]; // Default view is all transactions
      
      currentPage = 1;
      renderTransactionTable(filteredTransactions, currentPage);
      updatePaginationControls(filteredTransactions.length, currentPage);
      updateFilterDisplay();

      // Initialize DataTables.js if necessary
      if ($.fn.DataTable.isDataTable("#transactions-table")) {
        $("#transactions-table").DataTable().clear().destroy();
      }

      $("#transactions-table").DataTable({
        pageLength: pageSize,
        ordering: true,
        searching: false, // Disable DataTables' built-in search to use custom filters
        lengthChange: false,
        destroy: true,
      });
    } else {
      console.warn("No transactions available.");
      document.querySelector("#transactions-table tbody").innerHTML = `
        <tr><td colspan="7" style="text-align:center;">No transactions available</td></tr>
      `;
    }
  } catch (error) {
    console.error("Error initializing transactions table:", error);
  }
}

//----------------------------------------------------
// Render Transactions Table (Handles Pagination)
//----------------------------------------------------
function renderTransactionTable(transactions, page = 1) {
  const transactionsTable = document.querySelector("#transactions-table tbody");
  if (!transactionsTable) return;

  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const paginatedTransactions = transactions.slice(start, end);

  transactionsTable.innerHTML = paginatedTransactions
    .map(
      (tx) => `
        <tr>
          <td>${tx.date || "N/A"}</td>
          <td>${tx.amount !== undefined ? `$${parseFloat(tx.amount).toFixed(2)}` : "N/A"}</td>
          <td>${tx.name || "N/A"}</td>
          <td>${Array.isArray(tx.category) ? tx.category.join(", ") : tx.category || "Uncategorized"}</td>
          <td>${tx.merchant_name || "Unknown"}</td>
          <td>${tx.account_name || "Unknown Account"}</td>
          <td>${tx.institution_name || "Unknown Institution"}</td>
        </tr>`
    )
    .join("");

  updatePaginationControls(transactions.length, page);
}

//----------------------------------------------------
// Handle Pagination Changes
//----------------------------------------------------
function changePage(offset) {
  const totalPages = Math.ceil(filteredTransactions.length / pageSize);
  const newPage = Math.max(1, Math.min(currentPage + offset, totalPages));

  if (newPage !== currentPage) {
    currentPage = newPage;
    renderTransactionTable(filteredTransactions, currentPage);
    updatePaginationControls(filteredTransactions.length, currentPage);
  }
}

//----------------------------------------------------
// Update Pagination Controls
//----------------------------------------------------
function updatePaginationControls(totalItems, page) {
  const totalPages = Math.ceil(totalItems / pageSize);
  const pageIndicator = document.getElementById("pageIndicator");
  const prevButton = document.getElementById("prevPage");
  const nextButton = document.getElementById("nextPage");

  if (pageIndicator) {
    pageIndicator.textContent = totalPages > 0 ? `Page ${page} of ${totalPages}` : "No transactions";
  }

  if (prevButton) {
    prevButton.disabled = page === 1;
  }
  
  if (nextButton) {
    nextButton.disabled = page === totalPages || totalPages === 0;
  }
}

//----------------------------------------------------
// Filtering Functionality (Category Filtering)
//----------------------------------------------------
function filterTransactionsByCategory(category) {
  if (category === "All") {
    filteredTransactions = [...allTransactions];
  } else {
    filteredTransactions = allTransactions.filter((tx) => {
      if (Array.isArray(tx.category)) {
        return tx.category.includes(category); // Handles multi-category transactions
      }
      return tx.category === category;
    });
  }

  currentPage = 1; // ✅ Always reset to first page on filter change
  renderTransactionTable(filteredTransactions, currentPage);
  updatePaginationControls(filteredTransactions.length, currentPage);
}

//----------------------------------------------------
// Update Filter Display
//----------------------------------------------------
function updateFilterDisplay() {
  const filterLabel = document.getElementById("currentFilterLabel");
  if (filterLabel) {
    filterLabel.textContent = "Showing: All Categories";
  }
}

//----------------------------------------------------
// Setup Category Filter Menu (Event Delegation for Performance)
//----------------------------------------------------
function setupCategoryFilterMenu() {
  const filterMenu = document.getElementById("categoryFilterMenu");
  if (!filterMenu) return;

  filterMenu.addEventListener("click", (event) => {
    const selectedCategory = event.target.dataset.category;
    if (selectedCategory) {
      filterTransactionsByCategory(selectedCategory);
      updateFilterDisplay();
    }
  });
}
