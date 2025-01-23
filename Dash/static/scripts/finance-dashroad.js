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

  // 2. Transactions Table Logic
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

  // 3. Account Dropdown Logic
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

  // 4. Form Submission Handling
  if (refreshForm) {
    refreshForm.addEventListener('submit', event => {
      event.preventDefault();
      const selectedGroup = accountGroupSelect.value;

      fetch('/refresh_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ account_group: selectedGroup }),
      })
        .then(response => response.json())
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
