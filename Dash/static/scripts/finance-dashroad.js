// Below is a reorganized version of the user's JavaScript code.
// We have separated each main feature into its own function or block.
// This way, we can easily enable/disable each feature.
// The user asked to "split out each visual" so it can be easily toggled.
// We'll wrap them in functions and invoke them conditionally.

// The user also uses a DataTable for the transactions table, so we'll keep that in a separate function.

//----------------------------------------------------
// A small helper function for fetching data from the server.
//----------------------------------------------------
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

//----------------------------------------------------
// Transactions Table Setup
//----------------------------------------------------
async function initTransactionsTable() {
  const transactionsTable = document.querySelector("#transactions-table");
  if (!transactionsTable) return;

  try {
    const { status, data } = await fetchData("/get_transactions");
    if (status === "success") {
      const tableBody = transactionsTable.querySelector("tbody");
      tableBody.innerHTML = data.transactions
        .map(
          (tx) => `\n            <tr>\n              <td>${tx.date || "N/A"}</td>\n              <td>${tx.amount || "N/A"}</td>\n              <td>${tx.name || "N/A"}</td>\n              <td>${tx.category || "Uncategorized"}</td>\n              <td>${tx.merchant_name || "Unknown"}</td>\n              <td>${tx.account_name || "Unknown Account"}</td>\n              <td>${tx.institution_name || "Unknown Institution"}</td>\n            </tr>`
        )
        .join("");
          $(transactionsTable).DataTable({
            pageLength: 20, // Show 20 rows per page
            ordering: true, // Enable column sorting
            order: [[0, 'desc']], // Default sort by Date column (descending)
            columnDefs: [
                { type: 'num', targets: 4 } // Enable numeric sorting for Amount column
            ],
            language: {
                search: "Filter transactions:", // Custom search text
                emptyTable: "No transactions to display." // Custom empty table message
            },
            scrollY: "60vh", // Enable vertical scrolling for large datasets
            scrollCollapse: true, // Collapse the table to fit the container
        });
    }
  } catch (error) {
    console.error("Error initializing transactions table:", error);
    if (transactionsTable.querySelector("tbody")) {
      transactionsTable.querySelector("tbody").innerHTML = `<tr><td colspan="7">Error loading transactions.</td></tr>`;
    }
  }
}

//----------------------------------------------------
// Category Breakdown Chart (Pie ↔ Bar)
//----------------------------------------------------
let categoryChart; // hold reference to the Chart.js instance
let isCategoryPie = true;

async function renderCategoryChart() {
  const categoryCtx = document.getElementById("categoryBreakdownChart")?.getContext("2d");
  if (!categoryCtx) return;

  try {
    const { status, data } = await fetchData("/api/category_breakdown");
    if (status !== "success") return;

    // Prepare data
    const totalSpending = data.reduce((sum, entry) => sum + entry.amount, 0);
    const percentages = data.map((entry) => ((entry.amount / totalSpending) * 100).toFixed(2));
    const values = data.map((entry) => Math.round(entry.amount));
    const labels = data.map((entry) => entry.category);

    // Sort if using bar
    const sortedData = [...data].sort((a, b) => b.amount - a.amount);
    const sortedLabels = sortedData.map((entry) => entry.category);
    const sortedValues = sortedData.map((entry) => Math.round(entry.amount));

    // Destroy old chart if exists
    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(categoryCtx, {
      type: isCategoryPie ? "pie" : "bar",
      data: {
        labels: isCategoryPie ? labels : sortedLabels,
        datasets: [
          {
            label: isCategoryPie ? "Spending by Category (%)" : "Spending by Category ($)",
            data: isCategoryPie ? percentages : sortedValues,
            backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"],
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              label: (context) =>
                isCategoryPie
                  ? `${context.label}: ${context.raw}%`
                  : `${context.label}: $${context.raw.toLocaleString()}`,
            },
          },
        },
        ...(isCategoryPie
          ? {}
          : {
              indexAxis: "y",
              scales: {
                x: { beginAtZero: true },
              },
            }),
      },
    });
  } catch (error) {
    console.error("Error rendering category chart:", error);
  }
}

function toggleCategoryChart() {
  isCategoryPie = !isCategoryPie;
  renderCategoryChart();
}

//----------------------------------------------------
// Cash Flow Chart
//----------------------------------------------------
let cashFlowChart;
let isStackedView = true; // default to a stacked chart

async function renderCashFlowChart() {
  const cashFlowCtx = document.getElementById("cashFlowChart")?.getContext("2d");
  if (!cashFlowCtx) return;

  try {
    const { status, data } = await fetchData("/api/cash_flow");
    if (status !== "success") return;

    // Prepare data
    const labels = data.map((entry) => entry.month);
    const incomeData = data.map((entry) => Math.round(entry.income));
    const expenseData = data.map((entry) => -Math.round(entry.expenses)); // negative for expenses
    const netData = incomeData.map((val, idx) => val + expenseData[idx]);

    // Destroy old chart if exists
    if (cashFlowChart) cashFlowChart.destroy();

    // Decide which dataset(s) we show
    const datasets = isStackedView
      ? [
          {
            label: "Income",
            data: incomeData,
            backgroundColor: "#4BC0C0", // green-ish
          },
          {
            label: "Expenses",
            data: expenseData,
            backgroundColor: "#FF6384", // red-ish
          },
        ]
      : [
          {
            label: "Net Income",
            data: netData,
            backgroundColor: netData.map((value) => (value >= 0 ? "#4BC0C0" : "#FF6384")),
          },
        ];

    cashFlowChart = new Chart(cashFlowCtx, {
      type: "bar",
      data: {
        labels,
        datasets,
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                if (isStackedView) {
                  return `${context.dataset.label}: $${context.raw.toLocaleString()}`;
                }
                return `Net Income: $${context.raw.toLocaleString()}`;
              },
            },
          },
          datalabels: {
            anchor: "end",
            align: "top",
            formatter: (value) => `$${value.toLocaleString()}`,
            color: "#000",
            font: { weight: "bold" },
          },
        },
        scales: {
          x: {
            stacked: isStackedView,
            ticks: {
              autoSkip: false,
            },
          },
          y: {
            stacked: isStackedView,
            beginAtZero: true,
            ticks: {
              callback: (value) => `$${value.toLocaleString()}`,
            },
          },
        },
      },
    });
  } catch (error) {
    console.error("Error rendering cash flow chart:", error);
  }
}

function toggleCashFlowChart() {
  isStackedView = !isStackedView;
  renderCashFlowChart();
}

//----------------------------------------------------
// Document Ready (Init Functions)
//----------------------------------------------------
// We only call the init functions if we want them. This is how we can "enable/disable"
// each feature. You can wrap them in conditionals if needed.

document.addEventListener("DOMContentLoaded", async () => {
  // Table
  await initTransactionsTable();

  // Category Chart
  await renderCategoryChart();
  const toggleCategoryChartBtn = document.getElementById("toggleCategoryChart");
  if (toggleCategoryChartBtn) {
    toggleCategoryChartBtn.addEventListener("click", toggleCategoryChart);
  }

  // Cash Flow Chart
  await renderCashFlowChart();
  const toggleCashFlowChartBtn = document.getElementById("toggleCashFlowChart");
  if (toggleCashFlowChartBtn) {
    toggleCashFlowChartBtn.addEventListener("click", toggleCashFlowChart);
  }
});
