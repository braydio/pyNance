document.addEventListener("DOMContentLoaded", async () => {
    const cashFlowCtx = document.getElementById("cashFlowChart")?.getContext("2d");
  
    // Fetch Data Utility
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
  
    // Initialize the chart
    let cashFlowChart;
    let isNetView = false; // Toggle state for chart view
  
    if (cashFlowCtx) {
      try {
        const { status, data } = await fetchData("/api/cash_flow");
        if (status === "success") {
          const labels = data.map(entry => entry.month);
          const incomeData = data.map(entry => Math.round(entry.income));
          const spendingData = data.map(entry => Math.round(entry.expenses));
          const netData = data.map(entry => Math.round(entry.income - entry.expenses));
  
          // Render the initial chart in the "two-bar" view
          cashFlowChart = new Chart(cashFlowCtx, {
            type: "bar",
            data: {
              labels,
              datasets: [
                {
                  label: "Income",
                  data: incomeData,
                  backgroundColor: "#4BC0C0",
                },
                {
                  label: "Spending",
                  data: spendingData,
                  backgroundColor: "#FF6384",
                },
                {
                  label: "Net",
                  data: netData,
                  backgroundColor: "#FFCE56",
                },
              ],
            },
            options: {
              responsive: true,
              plugins: {
                legend: { display: true },
                tooltip: {
                  callbacks: {
                    label: context => {
                      const datasetLabel = context.dataset.label;
                      const value = context.raw || 0;
  
                      if (datasetLabel === "Net") {
                        const income = incomeData[context.dataIndex];
                        const spending = spendingData[context.dataIndex];
                        return [
                          `Net: $${value.toLocaleString()}`,
                          `Income: $${income.toLocaleString()}`,
                          `Spending: $${spending.toLocaleString()}`,
                        ];
                      }
  
                      return `${datasetLabel}: $${value.toLocaleString()}`;
                    },
                  },
                },
              },
              scales: {
                x: { ticks: { align: "center" }, title: { display: false } },
                y: {
                  beginAtZero: true,
                  ticks: {
                    callback: value => `$${value.toLocaleString()}`,
                  },
                  title: { display: false },
                },
              },
              onClick: toggleChartView, // Attach click handler
            },
          });
  
          // Toggle between two views: "Net" bar only and full dataset
          function toggleChartView() {
            isNetView = !isNetView; // Toggle state
  
            if (isNetView) {
              // Show only the Net bar
              cashFlowChart.data.datasets = [
                {
                  label: "Net",
                  data: netData,
                  backgroundColor: netData.map(value => (value >= 0 ? "#4BC0C0" : "#FF6384")),
                },
              ];
            } else {
              // Show Income, Spending, and Net bars
              cashFlowChart.data.datasets = [
                {
                  label: "Income",
                  data: incomeData,
                  backgroundColor: "#4BC0C0",
                },
                {
                  label: "Spending",
                  data: spendingData,
                  backgroundColor: "#FF6384",
                },
                {
                  label: "Net",
                  data: netData,
                  backgroundColor: "#FFCE56",
                },
              ];
            }
  
            // Update the chart
            cashFlowChart.update();
          }
        }
      } catch (error) {
        console.error("Error rendering cash flow chart:", error);
      }
    }
  });
  