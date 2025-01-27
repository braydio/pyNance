document.addEventListener("DOMContentLoaded", () => {
  // 1. Cash Flow Chart Logic
  const cashFlowCtx = document.getElementById('cashFlowChart')?.getContext('2d');

  if (cashFlowCtx) {
    fetch('/transactions')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          const transactions = data.data;

          // Process the data into monthly aggregates
          const monthlyData = transactions.reduce((acc, transaction) => {
            const date = new Date(transaction.date);
            const monthYear = `${date.getMonth() + 1}/${date.getFullYear()}`;
            acc[monthYear] = acc[monthYear] || { income: 0, spending: 0 };

            if (transaction.amount > 0) {
              acc[monthYear].income += transaction.amount;
            } else {
              acc[monthYear].spending += Math.abs(transaction.amount);
            }
            return acc;
          }, {});

          // Prepare data for the chart
          const labels = Object.keys(monthlyData).sort();
          const incomeData = labels.map(month => monthlyData[month].income);
          const spendingData = labels.map(month => monthlyData[month].spending);

          // Render the Cash Flow Chart
          new Chart(cashFlowCtx, {
            type: 'line',
            data: {
              labels,
              datasets: [
                {
                  label: 'Income',
                  data: incomeData,
                  borderColor: 'rgba(75, 192, 192, 1)',
                  backgroundColor: 'rgba(75, 192, 192, 0.2)',
                  fill: true,
                },
                {
                  label: 'Spending',
                  data: spendingData,
                  borderColor: 'rgba(255, 99, 132, 1)',
                  backgroundColor: 'rgba(255, 99, 132, 0.2)',
                  fill: true,
                },
              ],
            },
            options: {
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                tooltip: {
                  callbacks: {
                    label: tooltipItem =>
                      `${tooltipItem.dataset.label}: $${tooltipItem.raw.toFixed(2)}`,
                  },
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: { display: true, text: 'Amount (USD)' },
                },
                x: {
                  title: { display: true, text: 'Month/Year' },
                },
              },
            },
          });
        } else {
          console.error(data.message);
        }
      })
      .catch(error => console.error('Error fetching transactions:', error));
  }


  // 2. Net Income vs Spending Chart Logic
  const netIncomeCtx = document.getElementById('netIncomeSpendingChart')?.getContext('2d');

  if (netIncomeCtx) {
    fetch('/api/cash_flow')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          const labels = data.data.map(entry => entry.month);
          const incomeData = data.data.map(entry => Math.round(entry.income));
          const spendingData = data.data.map(entry => Math.round(entry.expenses));
  
          new Chart(netIncomeCtx, {
            type: 'bar',
            data: {
              labels,
              datasets: [
                {
                  label: 'Income',
                  data: incomeData,
                  backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
                {
                  label: 'Spending',
                  data: spendingData,
                  backgroundColor: 'rgba(255, 99, 132, 0.6)',
                },
              ],
            },
            options: {
              responsive: true,
              plugins: {
                legend: { display: false }, // Disable legend
                tooltip: {
                  callbacks: {
                    label: context => {
                      const value = context.raw || 0;
                      return `$${value.toLocaleString()}`; // Dollar formatting for tooltip
                    },
                  },
                },
                datalabels: {
                  anchor: 'end',
                  align: 'top',
                  formatter: value => `$${value.toLocaleString()}`, // Dollar formatting for labels
                  font: {
                    weight: 'bold',
                  },
                },
              },
              scales: {
                x: {
                  title: { display: false }, // Disable X-axis title
                },
                y: {
                  title: { display: false }, // Disable Y-axis title
                  beginAtZero: true,
                  ticks: {
                    callback: value => `$${value.toLocaleString()}`, // Y-axis dollar formatting
                  },
                },
              },
            },
            plugins: [ChartDataLabels], // Register the plugin
          });
        } else {
          console.error('Error in API response:', data.message);
        }
      })
      .catch(error => console.error('Error fetching cash flow data:', error));
  }
  



  // 3. Category Breakdown Chart Logic
  const categoryCtx = document.getElementById('categoryBreakdownChart')?.getContext('2d');

  if (categoryCtx) {
    fetch('/transactions')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          const transactions = data.data;
  
          // Process the data into categories
          const categoryData = transactions.reduce((acc, transaction) => {
            const category = transaction.category || 'Uncategorized';
            acc[category] = (acc[category] || 0) + Math.abs(transaction.amount);
            return acc;
          }, {});
  
          const labels = Object.keys(categoryData);
          const values = Object.values(categoryData).map(value => Math.round(value)); // Round values to whole numbers
  
          new Chart(categoryCtx, {
            type: 'pie',
            data: {
              labels,
              datasets: [
                {
                  label: 'Spending by Category',
                  data: values,
                  backgroundColor: [
                    '#FF6384', // Red
                    '#36A2EB', // Blue
                    '#FFCE56', // Yellow
                    '#4BC0C0', // Teal
                    '#9966FF', // Purple
                    '#FF9F40', // Orange
                  ],
                },
              ],
            },
            options: {
              responsive: true,
              plugins: {
                legend: { display: false }, // Disable legend
                tooltip: {
                  callbacks: {
                    label: context => {
                      const value = context.raw || 0;
                      return `${context.label}: $${value.toLocaleString()}`; // Format tooltip with dollar values
                    },
                  },
                },
                datalabels: {
                  formatter: (value, ctx) => `$${value.toLocaleString()}`, // Dollar formatting for labels
                  color: '#fff', // White text on labels
                  font: {
                    weight: 'bold',
                  },
                  anchor: 'center',
                  align: 'center',
                },
              },
            },
            plugins: [ChartDataLabels], // Register the plugin for labels
          });
        } else {
          console.error('Error in API response:', data.message);
        }
      })
      .catch(error => console.error('Error fetching transactions:', error));
  }
  

  // 4. Transactions Table Logic
  const transactionsTable = document.getElementById('transactions-table');
  if (transactionsTable) {
    fetch('/get_transactions')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          transactionsTable.innerHTML = data.data
            .map(
              tx => `
            <tr>
              <td>${tx.date}</td>
              <td>${tx.name}</td>
              <td>${tx.amount}</td>
            </tr>`
            )
            .join('');
        } else {
          console.error(data.message);
        }
      })
      .catch(error => console.error('Error fetching transactions:', error));
  }

  // 5. Account Dropdown Logic
  const refreshForm = document.getElementById('refresh-form');
  const accountGroupSelect = document.getElementById('account-group');

  if (accountGroupSelect) {
    fetch('/get_accounts')
      .then(response => response.json())
      .then(data => {
        data.groups.forEach(group => {
          const option = document.createElement('option');
          option.value = group.id;
          option.textContent = group.name;
          accountGroupSelect.appendChild(option);
        });
      })
      .catch(error => console.error('Error fetching account groups:', error));
  }

  // 6. Form Submission Handling
  if (refreshForm) {
    refreshForm.addEventListener('submit', event => {
      event.preventDefault();
  
      if (!accountGroupSelect) {
        console.error('Account group dropdown is missing from the DOM.');
        return;
      }
  
      const selectedGroup = accountGroupSelect.value;
      if (!selectedGroup) {
        alert('Please select a valid account group before refreshing.');
        return;
      }
  
      fetch('/refresh_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ account_group: selectedGroup }),
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.error) {
            alert(`Error: ${data.error}`);
          } else {
            alert('Data refreshed successfully!');
          }
        })
        .catch(error => console.error('Error refreshing data:', error));
    });
  }
});
