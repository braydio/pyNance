/**
 * accounts.js
 * A single, unified script for the /accounts page
 */

// References to DOM elements
let institutionsContainer,
  linkButton,
  statusContainer,
  groupNameInput,
  saveGroupButton,
  groupStatus;

// One-time on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded. Initializing app...");
  init();
});

/**
 * Plaid Link initialization
 */
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

        // Show Plaid Link immediately (or you could open it on button click)
        handler.open();
      } else {
        statusContainer.textContent = "Error fetching link token.";
      }
    })
    .catch((error) => {
      statusContainer.textContent = "Error initializing Plaid Link.";
      console.error(error);
    });
}

/**
 * Helper function to format date into d/mm/yyyy H:mm AM/PM
 */
function formatDateTime(timestamp) {
  if (!timestamp) return "Unknown"; // Handle cases where timestamp is null or undefined

  const date = new Date(timestamp);
  const options = {
    day: "numeric",
    month: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true, // Enable AM/PM format
  };

  return date.toLocaleString("en-GB", options); // Use en-GB to ensure d/mm/yyyy order
}

/**
 * Main initialization function
 */
function init() {
  // 1) Grab references to DOM elements
  institutionsContainer = document.getElementById("institutions-container");
  statusContainer = document.getElementById("status");
  groupNameInput = document.getElementById("group-name");
  saveGroupButton = document.getElementById("save-group");
  groupStatus = document.getElementById("group-status");
  linkButton = document.getElementById("link-button");

  if (saveGroupButton) {
    saveGroupButton.addEventListener("click", saveGroup);
  }

  // Attach Plaid Link event handler to linkButton if it exists
  if (linkButton) {
    linkButton.addEventListener("click", initializePlaidLink);
  }

  // Fetch institutions to populate UI
  if (institutionsContainer) {
    fetchAndRenderInstitutions();
  }

  console.log("App init complete");
}

/**
 * Fetch utility: returns a Promise resolving to JSON
 */
function fetchData(url, options = {}) {
  return fetch(url, options)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .catch((error) => {
      console.error(`Error fetching data from ${url}:`, error);
      throw error;
    });
}

/**
 * Fetch institutions and render them
 */
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

/**
 * Render institutions: displays each institution & accounts
 */
function renderInstitutions(institutions) {
  institutionsContainer.innerHTML = ""; // Clear old content

  Object.entries(institutions).forEach(([institutionName, details]) => {
    // Optionally sanitize institutionName before using it in an element ID
    const safeInstitutionName = institutionName.replace(/\s+/g, "-").toLowerCase();

    const institutionDiv = document.createElement("div");
    institutionDiv.className = "institution";
    const lastUpdatedFormatted = formatDateTime(details.last_successful_update);

    institutionDiv.innerHTML = `
      <div class="institution-header">
        <h3>${institutionName} (${details.accounts.length} accounts)</h3>
        <div>
          <span class="last-refresh">Last Updated: ${lastUpdatedFormatted}</span>
          <button class="refresh-accounts" data-item-id="${details.item_id}">Refresh</button>
        </div>
      </div>
      <div id="accounts-${safeInstitutionName}" class="accounts-container">
        ${details.accounts
          .map((acc) => {
            const balance = acc.balances.current || 0;
            const signClass = balance < 0 ? "negative" : "positive";
            return `
              <div class="account-item">
                <div class="account-details">
                  <span>${acc.account_name} (${acc.nickname || "No Nickname"})</span>
                  <span class="account-balance ${signClass}">$${balance.toLocaleString()}</span>
                </div>
                <small>${acc.subtype} - ${acc.type}</small>
              </div>
            `;
          })
          .join("")}
      </div>
      <div class="product-buttons" id="products-${details.item_id}">
      </div>
    `;

    // Generate product buttons for this institution
    generateProductButtons(details.item_id, details.products, institutionDiv);

    // Toggle the accounts on click of the institution header
    const header = institutionDiv.querySelector(".institution-header");
    header.addEventListener("click", (e) => {
      const refreshBtn = header.querySelector(".refresh-accounts");
      if (e.target === refreshBtn) return; // Avoid toggling if user clicks refresh
      toggleAccountsTable(safeInstitutionName);
    });

    // Attach refresh logic for the institution
    const refreshButton = institutionDiv.querySelector(".refresh-accounts");
    refreshButton.addEventListener("click", (event) => {
      event.stopPropagation(); // Don’t toggle accounts if clicking refresh
      refreshInstitution(details.item_id, institutionName);
    });

    institutionsContainer.appendChild(institutionDiv);
  });
}

/**
 * Generate product buttons for each institution
 */
function generateProductButtons(itemId, products, institutionDiv) {
  const productContainer = institutionDiv.querySelector(`#products-${itemId}`);
  products.forEach((product) => {
    const button = document.createElement("button");
    button.textContent = `Refresh ${product}`;
    button.classList.add("refresh-product-button");
    button.onclick = () => refreshProduct(itemId, product);
    productContainer.appendChild(button);
  });
}

/**
 * Call Flask API to refresh a specific product for an institution
 */
async function refreshProduct(itemId, product) {
  try {
    const response = await fetch("/refresh_item", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ item_id: itemId, product: product }),
    });

    const data = await response.json();
    if (data.status === "success") {
      alert(`${product} successfully refreshed for item ${itemId}`);
      fetchAndRenderInstitutions(); // Refresh UI after update
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (error) {
    console.error("Error refreshing product:", error);
    alert("Failed to refresh product. Check console for details.");
  }
}

/**
 * Toggle the accounts table for a given institution
 */
function toggleAccountsTable(safeInstitutionName) {
  const container = document.getElementById(`accounts-${safeInstitutionName}`);
  if (container) {
    container.style.display = container.style.display === "none" ? "block" : "none";
  }
}

/**
 * Refresh an institution's data
 */
function refreshInstitution(itemId, institutionName) {
  const button = document.querySelector(`button[data-item-id="${itemId}"]`);
  if (!button) return;

  button.disabled = true;
  button.textContent = "Refreshing...";

  fetchData("/refresh_account", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId }),
  })
    .then((res) => {
      if (res.status === "success") {
        alert(
          `Successfully refreshed ${institutionName}. Fetched ${res.transactions_fetched} transactions.`
        );
        fetchAndRenderInstitutions();
      } else if (res.status === "waiting") {
        alert(res.message);
      } else {
        alert(`Error refreshing account: ${res.error || "Unknown error"}`);
      }
      button.disabled = false;
      button.textContent = "Refresh";
    })
    .catch((error) => {
      console.error("Error refreshing account:", error);
      alert("Failed to refresh account.");
      button.disabled = false;
      button.textContent = "Refresh";
    });
}

/**
 * Save a group based on selected institutions
 */
function saveGroup() {
  const groupName = groupNameInput.value.trim();
  if (!groupName) {
    groupStatus.textContent = "Please enter a group name.";
    return;
  }

  // For this example, if you have any checkboxes for selected institutions:
  const selectedInstitutions = [];
  document.querySelectorAll(".institution-checkbox:checked").forEach((chk) => {
    selectedInstitutions.push(chk.dataset.itemId);
  });

  // POST to /save_group
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
