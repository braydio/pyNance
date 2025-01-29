document.addEventListener("DOMContentLoaded", async () => {
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

  // Transactions Table Setup
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
          pageLength: 20,
          ordering: true,
          dom: "Bfrtip",
          buttons: ["csv", "excel"],
        });
      }
    } catch (error) {
      console.error("Error initializing transactions table:", error);
      transactionsTable.querySelector("tbody").innerHTML = `<tr><td colspan="7">Error loading transactions.</td></tr>`;
    }
  }

  // 📌 Category Breakdown Chart Toggle (Pie ↔ Bar)
  const categoryCtx = document.getElementById("categoryBreakdownChart")?.getContext("2d");
  const toggleCategoryChartBtn = document.getElementById("toggleCategoryChart");
  let categoryChart;
  let isCategoryPie = true;

  async function renderCategoryChart() {
    if (!categoryCtx) return;

    try {
      const { status, data } = await fetchData("/api/category_breakdown");
      if (status !== "success") return;

      const totalSpending = data.reduce((sum, entry) => sum + entry.amount, 0);
      const percentages = data.map((entry) => ((entry.amount / totalSpending) * 100).toFixed(2));
      const values = data.map((entry) => Math.round(entry.amount));
      const labels = data.map((entry) => entry.category);

      const sortedData = [...data].sort((a, b) => b.amount - a.amount);
      const sortedLabels = sortedData.map((entry) => entry.category);
      const sortedValues = sortedData.map((entry) => Math.round(entry.amount));

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
                label: (context) => isCategoryPie ? `${context.label}: ${context.raw}%` : `${context.label}: $${context.raw.toLocaleString()}`
              },
            },
          },
          ...(isCategoryPie ? {} : { indexAxis: "y", scales: { x: { beginAtZero: true } } }),
        },
      });
    } catch (error) {
      console.error("Error rendering category chart:", error);
    }
  }

  if (toggleCategoryChartBtn) {
    toggleCategoryChartBtn.addEventListener("click", () => {
      isCategoryPie = !isCategoryPie;
      renderCategoryChart();
    });
  }

  await renderCategoryChart();

  const cashFlowCtx = document.getElementById("cashFlowChart")?.getContext("2d");
  const toggleCashFlowChartBtn = document.getElementById("toggleCashFlowChart");
  let cashFlowChart;
  let isStackedView = true; // Default: Net Income as a single stacked bar
  
  async function renderCashFlowChart() {
    if (!cashFlowCtx) return;
  
    try {
      const { status, data } = await fetchData("/api/cash_flow");
      if (status !== "success") return;
  
      const labels = data.map((entry) => entry.month);
      const incomeData = data.map((entry) => Math.round(entry.income));
      const expenseData = data.map((entry) => -Math.round(entry.expenses)); // Expenses always negative
      const netData = incomeData.map((value, index) => value + expenseData[index]); // Net = Income - Expenses
  
      if (cashFlowChart) cashFlowChart.destroy();
  
      const datasets = isStackedView
        ? [
            {
              label: "Income",
              data: incomeData,
              backgroundColor: "#4BC0C0", // Green
            },
            {
              label: "Expenses",
              data: expenseData,
              backgroundColor: "#FF6384", // Red
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
        data: { labels, datasets },
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
              ticks: { autoSkip: false }, // Show all months
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
  
  // Toggle Net Income Chart (Stacked ↔ Single Bar)
  if (toggleCashFlowChartBtn) {
    toggleCashFlowChartBtn.addEventListener("click", () => {
      isStackedView = !isStackedView;
      renderCashFlowChart();
    });
  }
  
  // Initial render
  await renderCashFlowChart();
  
});
