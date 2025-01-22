fetch('/get_transactions')
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      const transactions = data.data;
      let rows = '';
      transactions.forEach(tx => {
        rows += `<tr>
          <td>${tx.date}</td>
          <td>${tx.name}</td>
          <td>${tx.amount}</td>
        </tr>`;
      });
      document.getElementById('transactions-table').innerHTML = rows;
    } else {
      console.error(data.message);
    }
  })
  .catch(error => console.error('Error:', error));
