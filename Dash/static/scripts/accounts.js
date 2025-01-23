document.addEventListener("DOMContentLoaded", () => {
  const linkAccountButton = document.getElementById("link-account-button");
  const linkStatus = document.getElementById("link-status");
  const searchBar = document.getElementById("search-bar");
  const institutionsContainer = document.getElementById("institutions-container");
  const institutionSelect = document.getElementById("institution-select");
  const customGroupsContainer = document.getElementById("custom-groups-container");

  // Utility: Fetch data from an endpoint
  function fetchData(url, options = {}) {
    return fetch(url, options)
      .then(response => response.json())
      .catch(error => {
        console.error(`Error fetching data from ${url}:`, error);
        throw error;
      });
  }

  // Utility: Display loading indicator
  function toggleLoading(show) {
    const loadingIndicator = document.getElementById("loading-indicator");
    if (loadingIndicator) {
      loadingIndicator.style.display = show ? "block" : "none";
    }
  }

  // Fetch institutions and populate the dropdown
  fetchData("/get_accounts")
    .then(data => {
      data.groups.forEach(group => {
        const option = document.createElement("option");
        option.value = group.id;
        option.textContent = group.name;
        institutionSelect.appendChild(option);
      });
    })
    .catch(error => console.error("Error fetching account groups:", error));

  // Refresh all linked accounts
  window.refreshAllLinkedAccounts = () => {
    toggleLoading(true);
    fetchData("/refresh_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_all: true })
    })
      .then(data => {
        if (data.error) {
          alert(`Error: ${data.error}`);
        } else {
          alert("All accounts refreshed successfully!");
        }
      })
      .finally(() => toggleLoading(false))
      .catch(error => console.error("Error refreshing all accounts:", error));
  };

  // Refresh selected institutions
  window.refreshSelectedInstitutions = () => {
    const selectedInstitutions = Array.from(institutionSelect.selectedOptions).map(option => option.value);

    if (selectedInstitutions.length === 0) {
      alert("Please select at least one institution to refresh.");
      return;
    }

    toggleLoading(true);
    fetchData("/refresh_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ institutions: selectedInstitutions })
    })
      .then(data => {
        if (data.error) {
          alert(`Error: ${data.error}`);
        } else {
          alert("Selected institutions refreshed successfully!");
        }
      })
      .finally(() => toggleLoading(false))
      .catch(error => console.error("Error refreshing selected institutions:", error));
  };

  // Save custom groups
  window.saveCustomGroup = () => {
    const groupName = document.getElementById("group-name").value;
    const selectedInstitutions = Array.from(institutionSelect.selectedOptions).map(option => ({
      id: option.value,
      name: option.textContent,
    }));

    if (!groupName || selectedInstitutions.length === 0) {
      alert("Please provide a group name and select at least one institution.");
      return;
    }

    const customGroup = { name: groupName, institutions: selectedInstitutions };

    toggleLoading(true);
    fetchData("/save_group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customGroup)
    })
      .then(data => {
        if (data.error) {
          alert(`Error: ${data.error}`);
        } else {
          alert(`Group "${groupName}" saved successfully!`);
          displayCustomGroup(customGroup);
        }
      })
      .finally(() => toggleLoading(false))
      .catch(error => console.error("Error saving group:", error));
  };

  // Display saved custom groups
  const displayCustomGroup = group => {
    const groupDiv = document.createElement("div");
    groupDiv.className = "custom-group";

    const groupTitle = document.createElement("h3");
    groupTitle.textContent = group.name;

    const groupList = document.createElement("ul");
    group.institutions.forEach(inst => {
      const listItem = document.createElement("li");
      listItem.textContent = inst.name;
      groupList.appendChild(listItem);
    });

    groupDiv.appendChild(groupTitle);
    groupDiv.appendChild(groupList);
    customGroupsContainer.appendChild(groupDiv);
  };

  // Fetch and render institutions
  function fetchInstitutions() {
    fetchData("/get_institutions")
      .then(data => {
        if (data.status === "success") {
          renderInstitutions(data.institutions);
        } else {
          console.error("Error fetching institutions:", data.message);
          alert("Failed to fetch institutions.");
        }
      })
      .catch(error => console.error("Error fetching institutions:", error));
  }

  function renderInstitutions(institutions) {
    institutionsContainer.innerHTML = ""; // Clear previous content

    Object.keys(institutions).forEach(institutionName => {
      const institution = institutions[institutionName];
      const institutionRow = document.createElement("div");
      institutionRow.classList.add("institution-row");
      institutionRow.textContent = `${institutionName} (${institution.accounts.length} accounts)`;
      institutionRow.onclick = () => toggleAccounts(institutionName);

      const accountsTable = document.createElement("table");
      accountsTable.classList.add("hidden");
      accountsTable.id = `accounts-${institutionName}`;
      accountsTable.innerHTML = `
        <thead>
          <tr>
            <th>Account Name</th>
            <th>Type</th>
            <th>Subtype</th>
            <th>Available Balance</th>
            <th>Current Balance</th>
          </tr>
        </thead>
        <tbody>
          ${institution.accounts.map(account => `
            <tr>
              <td>${account.account_name}</td>
              <td>${account.type}</td>
              <td>${account.subtype}</td>
              <td>${account.balances.available || 'N/A'}</td>
              <td>${account.balances.current || 'N/A'}</td>
            </tr>
          `).join('')}
        </tbody>
      `;

      institutionsContainer.appendChild(institutionRow);
      institutionsContainer.appendChild(accountsTable);
    });
  }

  function toggleAccounts(institutionName) {
    const table = document.getElementById(`accounts-${institutionName}`);
    if (table) {
      table.classList.toggle("hidden");
    }
  }

  // Filter institutions
  function filterInstitutions() {
    const query = searchBar.value.toLowerCase();
    const rows = document.querySelectorAll(".institution-row");

    rows.forEach(row => {
      const institutionName = row.textContent.toLowerCase();
      row.style.display = institutionName.includes(query) ? "" : "none";
    });
  }

  // Fetch link token and initialize Plaid Link
  function fetchLinkToken() {
    fetchData("/get_link_token")
      .then(data => {
        if (data.link_token) {
          const handler = Plaid.create({
            token: data.link_token,
            onSuccess: (public_token, metadata) => {
              console.log("Public Token:", public_token);
              savePublicToken(public_token);
            },
            onExit: (err, metadata) => {
              if (err) {
                console.error("Plaid Link error:", err);
                updateStatus(linkStatus, "Error during account linking.", "error");
              } else {
                updateStatus(linkStatus, "Account linking process was exited.", "info");
              }
            },
          });

          if (linkAccountButton) {
            linkAccountButton.onclick = () => handler.open();
          }
        } else {
          updateStatus(linkStatus, `Failed to fetch link token: ${data.error}`, "error");
        }
      })
      .catch(error => {
        console.error("Error fetching link token:", error);
        updateStatus(linkStatus, "Error fetching link token.", "error");
      });
  }

  // Save public token to the backend
  function savePublicToken(public_token) {
    fetchData("/save_public_token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ public_token }),
    })
      .then(data => {
        if (data.access_token) {
          updateStatus(linkStatus, "Account linked successfully!", "success");
        } else {
          updateStatus(linkStatus, "Failed to link account.", "error");
        }
      })
      .catch(err => {
        console.error("Error saving public token:", err);
        updateStatus(linkStatus, "An error occurred while linking the account.", "error");
      });
  }

  // Update status message
  function updateStatus(element, message, statusClass) {
    element.textContent = message;
    element.className = statusClass;
  }

  // Initialize
  if (linkAccountButton) fetchLinkToken();
  if (searchBar) searchBar.addEventListener("input", filterInstitutions);
  if (institutionsContainer) fetchInstitutions();
});
