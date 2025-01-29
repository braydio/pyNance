// ----------------------------------------------------
// A small helper function for fetching data from the server.
// ----------------------------------------------------
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

// ----------------------------------------------------
// Transactions Table Setup
// ----------------------------------------------------
async function initTransactionsTable() {
  const transactionsTable = document.querySelector("#transactions-table");
  if (!transactionsTable) return;

  try {
    const { status, data } = await fetchData("/get_transactions");
    if (status === "success") {
      const tableBody = transactionsTable.querySelector("tbody");
      tableBody.innerHTML = data.transactions
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

// ----------------------------------------------------
// Category Breakdown Chart (Pie ↔ Bar)
// ----------------------------------------------------
let categoryChart; // hold reference to the Chart.js instance
let isCategoryPie = true;

async function renderCategoryChart() {
  const categoryCtx = document
    .getElementById("categoryBreakdownChart")
    ?.getContext("2d");
  if (!categoryCtx) return;

  try {
    const { status, data } = await fetchData("/api/category_breakdown");
    if (status !== "success") return;

    // Prepare data
    const totalSpending = data.reduce((sum, entry) => sum + entry.amount, 0);
    const percentages = data.map((entry) =>
      ((entry.amount / totalSpending) * 100).toFixed(2)
    );
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
            label: isCategoryPie
              ? "Spending by Category (%)"
              : "Spending by Category ($)",
            data: isCategoryPie ? percentages : sortedValues,
            backgroundColor: [
              "#FF6384",
              "#36A2EB",
              "#FFCE56",
              "#4BC0C0",
              "#9966FF",
              "#FF9F40",
            ],
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

// ----------------------------------------------------
// Cash Flow Chart (Income / Expenses / Net)
// ----------------------------------------------------
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
            backgroundColor: netData.map((value) =>
              value >= 0 ? "#4BC0C0" : "#FF6384"
            ),
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

// ----------------------------------------------------
// NEW: Net Assets vs. Liabilities Chart
// ----------------------------------------------------
let netAssetsChart;
let isNetAssetsStacked = true; // toggle stacked vs. net-only

async function renderNetAssetsChart() {
  const netAssetsCtx = document
    .getElementById("netAssetsChart")
    ?.getContext("2d");
  if (!netAssetsCtx) return;

  try {
    // Fetch data: assume /api/net_assets returns:
    // { status: 'success', data: [ { period:'2023-01', assets:20000, liabilities:5000 }, ... ] }
    const { status, data } = await fetchData("/api/net_assets");
    if (status !== "success") return;

    // Prepare data
    const labels = data.map((entry) => entry.period);
    const assetsData = data.map((entry) => Math.round(entry.assets));
    // We'll store liabilities as negative for a stacked approach
    const liabilitiesData = data.map((entry) => -Math.round(entry.liabilities));
    const netData = assetsData.map(
      (val, idx) => val + liabilitiesData[idx] // assets + (negative liabilities)
    );

    // Destroy old chart if exists
    if (netAssetsChart) netAssetsChart.destroy();

    // Decide which dataset(s) to show
    const datasets = isNetAssetsStacked
      ? [
          {
            label: "Assets",
            data: assetsData,
            backgroundColor: "#4BC0C0", // green-ish
          },
          {
            label: "Liabilities",
            data: liabilitiesData,
            backgroundColor: "#FF6384", // red-ish
          },
        ]
      : [
          {
            label: "Net Assets",
            data: netData,
            backgroundColor: netData.map((value) =>
              value >= 0 ? "#4BC0C0" : "#FF6384"
            ),
          },
        ];

    netAssetsChart = new Chart(netAssetsCtx, {
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
                if (isNetAssetsStacked) {
                  // If stacked view, label assets vs liabilities
                  return `${context.dataset.label}: $${context.raw.toLocaleString()}`;
                }
                // Otherwise single bar for net
                return `Net Assets: $${context.raw.toLocaleString()}`;
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
            stacked: isNetAssetsStacked,
            ticks: {
              autoSkip: false,
            },
          },
          y: {
            stacked: isNetAssetsStacked,
            beginAtZero: true,
            ticks: {
              callback: (val) => `$${val.toLocaleString()}`,
            },
          },
        },
      },
    });
  } catch (error) {
    console.error("Error rendering Net Assets chart:", error);
  }
}

function toggleNetAssetsChart() {
  isNetAssetsStacked = !isNetAssetsStacked;
  renderNetAssetsChart();
}

// ----------------------------------------------------
// Document Ready (Init Functions)
// ----------------------------------------------------
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

  // Net Assets vs. Liabilities Chart
  await renderNetAssetsChart();
  const toggleNetAssetsBtn = document.getElementById("toggleNetAssetsChart");
  if (toggleNetAssetsBtn) {
    toggleNetAssetsBtn.addEventListener("click", toggleNetAssetsChart);
  }
});
