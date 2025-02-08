let allTransactions = []; // will hold all transaction data
//----------------------------------------------------
// Transactions Table Setup
//----------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
    await initTransactionsTable();
    setupCategoryFilterMenu(); // Initialize the filter menu
});

//----------------------------------------------------
// A small helper function for fetching data from the server.
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
    if (status === "success") {
      allTransactions = data.transactions;
      currentPage = 1; 
      renderTransactionTable(allTransactions, currentPage);
      updatePaginationControls(allTransactions.length, currentPage);
      updateFilterDisplay();

      // Apply DataTables.js (Only if transactions exist)
      if ($.fn.DataTable.isDataTable("#transactions-table")) {
        $("#transactions-table").DataTable().clear().destroy();
      }
      
      $("#transactions-table").DataTable({
        pageLength: pageSize,  // Ensure page size matches pagination
        ordering: true,  // Enable sorting
        searching: true, // Enable filtering
        lengthChange: false, // Hide "Show entries" dropdown
        destroy: true
      });
    }
  } catch (error) {
    console.error("Error initializing transactions table:", error);
  }
}

  
let currentPage = 1;
const pageSize = 15; // 15 items per page

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
          <td>${tx.amount || "N/A"}</td>
          <td>${tx.name || "N/A"}</td>
          <td>${tx.category || "Uncategorized"}</td>
          <td>${tx.merchant_name || "Unknown"}</td>
          <td>${tx.account_name || "Unknown Account"}</td>
          <td>${tx.institution_name || "Unknown Institution"}</td>
        </tr>`
    )
    .join("");

  updatePaginationControls(transactions.length, page);
}
  
function changePage(offset) {
  const totalPages = Math.ceil(allTransactions.length / pageSize);
  const newPage = Math.max(1, Math.min(currentPage + offset, totalPages));

  if (newPage !== currentPage) {
    currentPage = newPage;
    renderTransactionTable(allTransactions, currentPage);
    updatePaginationControls(allTransactions.length, currentPage);
  }
}

function updatePaginationControls(totalItems, page) {
  const totalPages = Math.ceil(totalItems / pageSize);
  const pageIndicator = document.getElementById("pageIndicator");
  const prevButton = document.getElementById("prevPage");
  const nextButton = document.getElementById("nextPage");

  if (pageIndicator) {
    pageIndicator.textContent = `Page ${page} of ${totalPages}`;
  }

  if (prevButton) {
    prevButton.disabled = page === 1;
  }
  
  if (nextButton) {
    nextButton.disabled = page === totalPages;
  }
}


//----------------------------------------------------
// A stub function to update the filter display if needed.
// Modify this function to suit your UI needs.
//----------------------------------------------------
function updateFilterDisplay() {
    // For example, update a label to show the current filter.
    const filterLabel = document.getElementById("currentFilterLabel");
    if (filterLabel) {
      filterLabel.textContent = "Showing: All Categories";
    }
}

// ----------------------------------------------------
// Filtering Functionality
// ----------------------------------------------------
function filterTransactionsByCategory(category) {
  let filtered;

  if (category === "All") {
    filtered = allTransactions;
  } else {
    filtered = allTransactions.filter((tx) => tx.category === category);
  }

  currentPage = 1; // ✅ Always reset to first page on filter change
  renderTransactionTable(filtered, currentPage);
  updatePaginationControls(filtered.length, currentPage);
}

