document.addEventListener("DOMContentLoaded", async () => {
  // Utility to fetch data
  async function fetchData(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`Error fetching data from ${url}:`, error);
      throw error;
    }
  }

  // Render Transactions Table
  const transactionsTable = document.querySelector("#transactions-table");
  if (transactionsTable) {
    try {
      const { status, data } = await fetchData("/get_transactions");
      if (status === "success") {
        const tableBody = transactionsTable.querySelector("tbody");
        tableBody.innerHTML = data.transactions
          .map(
            (tx) => `
            <tr>
              <td>${tx.date}</td>
              <td>${tx.amount}</td>
              <td>${tx.name}</td>
              <td>${tx.category}</td>
              <td>${tx.merchant_name}</td>
              <td>${tx.account_name}</td>
              <td>${tx.institution_name}</td>
            </tr>`
          )
          .join("");

        // Initialize DataTable
        $(transactionsTable).DataTable({
          pageLength: 20,
          ordering: true,
          order: [[0, "desc"]],
          columnDefs: [{ type: "num", targets: 1 }], // Ensure Amount is numeric
          language: {
            search: "Filter transactions:",
            emptyTable: "No transactions available.",
          },
          scrollY: "60vh",
          scrollCollapse: true,
          dom: "Bfrtip",
          buttons: ["csv", "excel", "pdf"],
        });
      }
    } catch (error) {
      console.error("Error initializing transactions table:", error);
    }
  }
});