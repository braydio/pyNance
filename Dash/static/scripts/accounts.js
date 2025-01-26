document.addEventListener("DOMContentLoaded", () => {
  const institutionsContainer = document.getElementById("institutions-container");
  const linkButton = document.getElementById("link-button");
  const statusContainer = document.getElementById("status");
  const groupNameInput = document.getElementById("group-name");
  const saveGroupButton = document.getElementById("save-group");
  const groupStatus = document.getElementById("group-status");

  // Utility to fetch data from an endpoint
  function fetchData(url, options = {}) {
    return fetch(url, options)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        console.error(`Error fetching data from ${url}:`, error);
        throw error;
      });
  }

  // Plaid Link functionality
  function initializePlaidLink() {
    fetchData("/get_link_token")
      .then((data) => {
        if (data.link_token) {
          const handler = Plaid.create({
            token: data.link_token,
            onSuccess: function (public_token, metadata) {
              console.log("Public Token:", public_token);

              fetchData("/save_public_token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ public_token }),
              })
                .then((response) => {
                  if (response.access_token) {
                    statusContainer.textContent = "Access token received!";
                  } else {
                    console.error("Error saving public token:", response.error);
                    statusContainer.textContent = "Failed to save public token.";
                  }
                })
                .catch((error) => {
                  console.error("Error saving public token:", error);
                  statusContainer.textContent = "An error occurred.";
                });
            },
            onExit: function (err, metadata) {
              if (err) {
                statusContainer.textContent = "User exited with an error.";
              } else {
                statusContainer.textContent = "User exited without error.";
              }
            },
          });

          linkButton.onclick = () => handler.open();
        } else {
          statusContainer.textContent = "Error fetching link token.";
        }
      })
      .catch((error) => {
        statusContainer.textContent = "Error initializing Plaid Link.";
      });
  }

  // Fetch institutions and render them with institution-level checkboxes
  function fetchAndRenderInstitutions() {
    fetchData("/get_institutions")
      .then((data) => {
        if (data.status === "success") {
          renderInstitutions(data.institutions);
        } else {
          institutionsContainer.innerHTML = `<p>Error loading institutions: ${data.message}</p>`;
        }
      })
      .catch((error) => {
        institutionsContainer.innerHTML = `<p>Error loading institutions.</p>`;
        console.error("Error:", error);
      });
  }

  // Render institutions with checkboxes and toggleable tables
  function renderInstitutions(institutions) {
  institutionsContainer.innerHTML = ""; // Clear existing content

  Object.keys(institutions).forEach((institutionName) => {
    const institution = institutions[institutionName];

    // Create the container for each institution
    const institutionDiv = document.createElement("div");
    institutionDiv.className = "institution";

    // Create the header for the institution
    const institutionHeader = document.createElement("div");
    institutionHeader.className = "institution-row";
    institutionHeader.innerHTML = `
      <input type="checkbox" class="institution-checkbox" data-item-id="${institution.item_id}" />
      <h3>${institutionName} (${institution.accounts.length} accounts)</h3>
      <button class="refresh-institution" data-institution-id="${institution.item_id}">Refresh</button>
    `;

    // Add toggle functionality to the header
    institutionHeader.addEventListener("click", (event) => {
      if (!event.target.classList.contains("institution-checkbox")) {
        toggleAccountsTable(institutionName); // Toggle accounts table when clicking the header
      }
    });

    // Create the table for accounts
    const accountsTable = document.createElement("table");
    accountsTable.className = "hidden"; // Initially hidden
    accountsTable.id = `accounts-${institutionName}`;
    accountsTable.innerHTML = `
      <thead>
        <tr>
          <th>Account Name</th>
          <th>Subtype</th>
          <th>Balance</th>
        </tr>
      </thead>
      <tbody>
        ${institution.accounts
          .map((account) => {
            const balance = account.balances.current || 0;
            const balanceClass = balance < 0 ? "negative" : "positive";
            return `
              <tr>
                <td>${account.account_name}</td>
                <td>${account.subtype}</td>
                <td class="${balanceClass}">${balance.toLocaleString("en-US", {
              style: "currency",
              currency: "USD",
            })}</td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    `;

    // Append the institution header and accounts table
    institutionDiv.appendChild(institutionHeader);
    institutionDiv.appendChild(accountsTable);
    institutionsContainer.appendChild(institutionDiv);

    // Add refresh button functionality
    const refreshButton = institutionHeader.querySelector(".refresh-institution");
    refreshButton.addEventListener("click", (event) => {
      event.stopPropagation(); // Prevent toggle when clicking refresh
      refreshInstitution(institution.item_id, institutionName);
    });
  });
  }

  // Save a group based on selected institutions
  function saveGroup() {
    const groupName = groupNameInput.value.trim();
    if (!groupName) {
      groupStatus.textContent = "Please enter a group name.";
      return;
    }

    const selectedInstitutions = Array.from(document.querySelectorAll(".institution-checkbox:checked"))
      .map((checkbox) => checkbox.dataset.itemId);

    if (selectedInstitutions.length === 0) {
      groupStatus.textContent = "Please select at least one institution.";
      return;
    }

    // Send group data to the backend
    fetchData("/save_group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ groupName, itemIds: selectedInstitutions }),
    })
      .then((response) => {
        if (response.status === "success") {
          groupStatus.textContent = `Group "${groupName}" saved successfully!`;
        } else {
          groupStatus.textContent = `Failed to save group: ${response.message}`;
        }
      })
      .catch((error) => {
        groupStatus.textContent = "An error occurred while saving the group.";
        console.error("Error saving group:", error);
      });
  }

  // Toggle accounts table
  function toggleAccountsTable(institutionName) {
    const table = document.getElementById(`accounts-${institutionName}`);
    if (table) {
      table.classList.toggle("hidden");
    }
  }

  // Refresh an institution's data
  function refreshInstitution(institutionId, institutionName) {
    const refreshButton = document.querySelector(
      `button[data-institution-id="${institutionId}"]`
    );
    refreshButton.disabled = true;
    refreshButton.textContent = "Refreshing...";

    fetchData("/refresh_account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: institutionId }),
    })
      .then((response) => {
        refreshButton.disabled = false;
        refreshButton.textContent = "Refresh";
        if (response.status === "success") {
          alert(`Institution "${institutionName}" refreshed successfully!`);
          fetchAndRenderInstitutions();
        } else {
          alert(`Error refreshing "${institutionName}": ${response.error}`);
        }
      })
      .catch((error) => {
        refreshButton.disabled = false;
        refreshButton.textContent = "Refresh";
        alert(`Error refreshing "${institutionName}": ${error.message}`);
      });
  }

  // Initialize
  if (linkButton) initializePlaidLink();
  if (saveGroupButton) saveGroupButton.addEventListener("click", saveGroup);
  if (institutionsContainer) fetchAndRenderInstitutions();
});
