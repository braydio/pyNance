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

  document.addEventListener("DOMContentLoaded", () => {
    const refreshForm = document.getElementById("refresh-form");
    const accountGroupSelect = document.getElementById("account-group");
  
    // Fetch account groups to populate the dropdown
    fetch("/get_accounts")
      .then((response) => response.json())
      .then((data) => {
        data.groups.forEach((group) => {
          const option = document.createElement("option");
          option.value = group.id;
          option.textContent = group.name;
          accountGroupSelect.appendChild(option);
        });
      })
      .catch((error) => console.error("Error fetching account groups:", error));
  
    // Handle form submission
    refreshForm.addEventListener("submit", (event) => {
      event.preventDefault();
  
      const selectedGroup = accountGroupSelect.value;
  
      fetch("/refresh_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ account_group: selectedGroup }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            alert(`Error: ${data.error}`);
          } else {
            alert("Data refreshed successfully!");
            // Optionally, refresh the UI or reload specific sections
          }
        })
        .catch((error) => console.error("Error refreshing data:", error));
    });
  });
  