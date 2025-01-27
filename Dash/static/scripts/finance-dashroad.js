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

  // Utility to render charts
  function renderChart(ctx, type, labels, datasets, options = {}) {
    new Chart(ctx, {
      type,
      data: { labels, datasets },
      options,
    });
  }

  // Base chart options
  const baseChartOptions = {
    responsive: true,
    plugins: {
      legend: { display: true }, // Show legend by default
      tooltip: {
        callbacks: {
          label: context => `$${context.raw.toLocaleString()}`, // Format tooltips
        },
      },
    },
    scales: {
      x: { ticks: { align: "center" }, title: { display: false } }, // Center X-axis labels
      y: {
        beginAtZero: true,
        ticks: {
          callback: value => `$${value.toLocaleString()}`, // Format Y-axis values
        },
        title: { display: false }, // Hide Y-axis title
      },
    },
  };

  // 1. Render Cash Flow Chart
  const cashFlowCtx = document.getElementById("cashFlowChart")?.getContext("2d");
  if (cashFlowCtx) {
    try {
      const { status, data } = await fetchData("/api/cash_flow");
      if (status === "success") {
        const labels = data.map(entry => entry.month);
        const incomeData = data.map(entry => Math.round(entry.income));
        const spendingData = data.map(entry => Math.round(entry.expenses));
        const netData = data.map(entry => Math.round(entry.income - entry.expenses));

        renderChart(
          cashFlowCtx,
          "bar", // Bar chart type
          labels,
          [
            { label: "Income", data: incomeData, backgroundColor: "#4BC0C0" },
            { label: "Spending", data: spendingData, backgroundColor: "#FF6384" },
            { label: "Net", data: netData, backgroundColor: "#FFCE56" },
          ],
          {
            ...baseChartOptions,
            plugins: {
              ...baseChartOptions.plugins,
              tooltip: {
                callbacks: {
                  label: context => {
                    const datasetLabel = context.dataset.label;
                    const value = context.raw || 0;

                    if (datasetLabel === "Net") {
                      // Tooltip for Net Bar
                      const income = incomeData[context.dataIndex];
                      const spending = spendingData[context.dataIndex];
                      return [
                        `Net: $${value.toLocaleString()}`,
                        `Income: $${income.toLocaleString()}`,
                        `Spending: $${spending.toLocaleString()}`,
                      ];
                    }

                    // Tooltip for Income or Spending
                    return `${datasetLabel}: $${value.toLocaleString()}`;
                  },
                },
              },
            },
          }
        );
      }
    } catch (error) {
      console.error("Error rendering cash flow chart:", error);
    }
  }

  // 2. Render Category Breakdown Chart
  const categoryCtx = document.getElementById("categoryBreakdownChart")?.getContext("2d");
  if (categoryCtx) {
    try {
      const { status, data } = await fetchData("/get_transactions");
      if (status === "success") {
        const categoryData = data.reduce((acc, tx) => {
          const category = tx.category || "Uncategorized";
          acc[category] = (acc[category] || 0) + Math.abs(tx.amount);
          return acc;
        }, {});

        const labels = Object.keys(categoryData);
        const values = Object.values(categoryData).map(value => Math.round(value));

        renderChart(
          categoryCtx,
          "pie",
          labels,
          [
            {
              label: "Spending by Category",
              data: values,
              backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"],
            },
          ],
          baseChartOptions
        );
      }
    } catch (error) {
      console.error("Error rendering category breakdown chart:", error);
    }
  }

  // 3. Initialize Transactions Table
  const transactionsTable = document.querySelector("#transactions-table");
  if (transactionsTable) {
    try {
      const { status, data } = await fetchData("/get_transactions");
      if (status === "success") {
        const tableBody = transactionsTable.querySelector("tbody");
        tableBody.innerHTML = data
          .map(
            tx => `
            <tr>
              <td>${tx.date}</td>
              <td>${tx.name}</td>
              <td>${tx.amount}</td>
            </tr>`
          )
          .join("");

        // Initialize DataTable
        $(transactionsTable).DataTable({
          pageLength: 20,
          ordering: true,
          order: [[0, "desc"]], // Sort by Date (descending)
          columnDefs: [{ type: "num", targets: 2 }], // Numeric sorting for Amount column
          language: {
            search: "Filter transactions:",
            emptyTable: "No transactions available.",
          },
          scrollY: "60vh", // Enable vertical scrolling
          scrollCollapse: true,
          dom: "Bfrtip", // Add export buttons
          buttons: ["csv", "excel", "pdf"], // Export buttons
        });
      }
    } catch (error) {
      console.error("Error initializing transactions table:", error);
    }
  }
});
