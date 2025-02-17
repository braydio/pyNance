<template>
  <div class="accounts-page">
    <header>
      <div>
        <h1>Accounts</h1>
        <h3>dot Brayden.com</h3>
      </div>
      <nav class="menu">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/teller-dot">Teller.IO</router-link>
        <router-link to="/accounts">Accounts</router-link>
        <router-link to="/transactions">Transactions</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </header>

    <main>
      <!-- Controls Section -->
      <div class="controls">
        <div id="account-management-header">
          <h2>Account Management</h2>
          <p>
            View and manage your accounts by institution. You can refresh account data,
            view balances, and create groups.
          </p>
          <button @click="initializePlaidLink">Link New Account</button>
        </div>
        <div id="group-management">
          <h2>Create a Group</h2>
          <p>Select institutions to add them to a refresh group:</p>
          <input type="text" v-model="groupName" placeholder="Enter group name" />
          <button @click="saveGroup">Save Group</button>
          <p id="group-status">{{ groupStatus }}</p>
        </div>
      </div>

      <!-- Institutions List -->
      <div id="institutions-container">
        <div v-if="institutions.length === 0">
          <p>No institutions available.</p>
        </div>
        <div v-for="inst in institutions" :key="inst.item_id" class="institution">
          <div class="institution-header" @click="toggleInstitution(inst)">
            <h3>
              {{ inst.institution_name }} ({{ inst.accounts.length }} accounts)
            </h3>
            <div>
              <span class="last-refresh">
                Last Updated: {{ inst.last_successful_update || 'Never refreshed' }}
              </span>
              <button @click.stop="refreshInstitution(inst.item_id, inst.institution_name)">
                Refresh
              </button>
            </div>
          </div>
          <div class="accounts-container" v-show="inst.expanded">
            <div
              v-for="acc in inst.accounts"
              :key="acc.account_id"
              class="account-item"
            >
              <div class="account-details">
                <span>
                  {{ acc.account_name }} ({{ acc.nickname || 'No Nickname' }})
                </span>
                <span
                  class="account-balance"
                  :class="{'negative': acc.balance < 0, 'positive': acc.balance >= 0}"
                >
                  ${{ acc.balance.toLocaleString() }}
                </span>
              </div>
              <small>{{ acc.subtype }} - {{ acc.type }}</small>
              <button @click="deleteAccount(acc.account_id)">Delete</button>
            </div>
          </div>
          <!-- Product Refresh Buttons -->
          <div class="product-buttons">
            <div v-for="prod in inst.products" :key="prod">
              <button @click="refreshProduct(inst.item_id, prod)">
                Refresh {{ prod }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div id="status">{{ statusMessage }}</div>
    </main>

    <footer>&copy; Brayden's Finance Dashroad</footer>
  </div>
</template>

<script>
import axios from "axios";
import { ref, onMounted } from "vue";

export default {
  name: "Accounts",
  setup() {
    const institutions = ref([]);
    const statusMessage = ref("");
    const groupName = ref("");
    const groupStatus = ref("");

    // Fetch institutions from backend API
    const fetchInstitutions = async () => {
      try {
        const res = await axios.get("/get_institutions");
        if (res.data.status === "success") {
          // Convert institutions object into an array and add an "expanded" flag.
          institutions.value = Object.values(res.data.institutions).map((inst) => ({
            ...inst,
            expanded: false,
          }));
        } else {
          statusMessage.value = "Error loading institutions: " + res.data.message;
        }
      } catch (error) {
        console.error("Error fetching institutions:", error);
        statusMessage.value = "Error loading institutions.";
      }
    };

    // Initialize Plaid Link to add a new account.
    const initializePlaidLink = async () => {
      try {
        // Call API to get the link token for linking transactions.
        const res = await axios.get("/plaid_link_transactions");
        if (res.data.link_token) {
          // Use the global Plaid Link library (assumed loaded via a script tag)
          const handler = Plaid.create({
            token: res.data.link_token,
            onSuccess: async (public_token, metadata) => {
              console.log("Public Token:", public_token);
              // Exchange public token for an access token
              const exchangeRes = await axios.post("/public_transactions_token", {
                public_token,
              });
              if (exchangeRes.data.access_token) {
                statusMessage.value = "Access token received!";
                // Refresh institutions after linking new account.
                fetchInstitutions();
              } else {
                statusMessage.value = "Failed to save public token.";
              }
            },
            onExit: (err, metadata) => {
              statusMessage.value = err
                ? "User exited with an error."
                : "User exited without error.";
            },
          });
          handler.open();
        } else {
          statusMessage.value = "Error fetching link token.";
        }
      } catch (error) {
        console.error("Error initializing Plaid Link:", error);
        statusMessage.value = "Error initializing Plaid Link.";
      }
    };

    // Toggle accounts table visibility for a given institution.
    const toggleInstitution = (inst) => {
      inst.expanded = !inst.expanded;
    };

    // Refresh institution accounts/transactions.
    const refreshInstitution = async (itemId, institutionName) => {
      try {
        statusMessage.value = `Refreshing ${institutionName}…`;
        const res = await axios.post("/transactions_refresh", { item_id: itemId });
        if (res.data.status === "success") {
          alert(
            `Successfully refreshed ${institutionName}. Fetched ${res.data.transactions_fetched} transactions.`
          );
          fetchInstitutions();
        } else {
          alert("Error: " + (res.data.error || "Unknown error"));
        }
      } catch (error) {
        console.error("Error refreshing institution:", error);
        alert("Failed to refresh institution.");
      }
    };

    // Refresh a specific product for an institution.
    const refreshProduct = async (itemId, product) => {
      try {
        const res = await axios.post("/refresh_transactions", {
          item_id: itemId,
          product: product,
        });
        if (res.data.status === "success") {
          alert(`${product} successfully refreshed for item ${itemId}`);
          fetchInstitutions();
        } else {
          alert(`Error: ${res.data.error}`);
        }
      } catch (error) {
        console.error("Error refreshing product:", error);
        alert("Failed to refresh product. Check console for details.");
      }
    };

    // Delete an account.
    const deleteAccount = async (accountId) => {
      if (!confirm("Are you sure you want to delete this account?")) return;
      try {
        const res = await axios.post("/delete_account", { account_id: accountId });
        if (res.data.status === "success") {
          alert(`Account ${accountId} deleted successfully.`);
          fetchInstitutions();
        } else {
          alert(`Error deleting account: ${res.data.error}`);
        }
      } catch (error) {
        console.error("Error deleting account:", error);
        alert("Failed to delete account. Check console for details.");
      }
    };

    // Save a group of institutions/accounts.
    const saveGroup = async () => {
      if (!groupName.value.trim()) {
        groupStatus.value = "Please enter a group name.";
        return;
      }
      // For example, send all institution item_ids (adjust as needed)
      const itemIds = institutions.value.map((inst) => inst.item_id);
      try {
        const res = await axios.post("/save_group", {
          groupName: groupName.value,
          accountIds: itemIds,
        });
        if (res.data.status === "success") {
          groupStatus.value = `Group "${groupName.value}" saved successfully!`;
        } else {
          groupStatus.value = "Failed to save group: " + res.data.message;
        }
      } catch (error) {
        console.error("Error saving group:", error);
        groupStatus.value = "An error occurred while saving the group.";
      }
    };

    // On mounted, fetch institutions.
    onMounted(() => {
      fetchInstitutions();
    });

    return {
      institutions,
      statusMessage,
      groupName,
      groupStatus,
      initializePlaidLink,
      fetchInstitutions,
      toggleInstitution,
      refreshInstitution,
      refreshProduct,
      deleteAccount,
      saveGroup,
    };
  },
};
</script>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f2f2f2;
}
nav.menu {
  display: flex;
  gap: 10px;
}
.controls {
  margin: 20px;
}
#institutions-container .institution {
  margin-bottom: 15px;
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow: hidden;
}
.institution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #1d1c22;
  color: #fff;
  padding: 10px;
  cursor: pointer;
}
.last-refresh {
  font-size: 0.9em;
  margin-right: 10px;
}
.accounts-container {
  padding: 10px;
  background: #f9f9f9;
}
.account-item {
  padding: 5px;
  border-bottom: 1px solid #ddd;
}
.account-details {
  display: flex;
  justify-content: space-between;
}
.account-balance.negative {
  color: red;
}
.account-balance.positive {
  color: green;
}
.product-buttons {
  padding: 10px;
  background: #eee;
  text-align: right;
}
button {
  margin: 5px;
  padding: 5px 10px;
  border: none;
  background: #3498db;
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
}
</style>
