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
      <div class="controls">
        <div id="account-management-header">
          <h2>Account Management</h2>
          <p>
            View and manage your accounts by institution. You can refresh account
            data, view balances, and create groups.
          </p>
          <button @click="linkNewAccount">Link New Account</button>
        </div>
        <div id="group-management">
          <h2>Create a Group</h2>
          <p>Select institutions to add them to a refresh group:</p>
          <input
            type="text"
            v-model="groupName"
            placeholder="Enter group name"
          />
          <button @click="saveGroup">Save Group</button>
          <p id="group-status">{{ groupStatus }}</p>
        </div>
      </div>

      <div id="institutions-container">
        <!-- Loop through institutions (populated from the API) -->
        <div
          v-for="inst in institutions"
          :key="inst.item_id"
          class="institution"
        >
          <div class="institution-header" @click="toggleInstitution(inst)">
            <h3>{{ inst.institution_name }}</h3>
            <span class="last-refresh">
              Last updated: {{ inst.last_successful_update || 'Never refreshed' }}
            </span>
          </div>
          <div
            class="accounts-container"
            v-show="inst.expanded"
          >
            <div
              v-for="acc in inst.accounts"
              :key="acc.id"
              class="account-item"
            >
              <div class="account-details">
                <span>{{ acc.name }}</span>
                <span class="account-balance">{{ acc.balance }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
    <footer>&copy; Brayden's Finance Dashroad</footer>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "Accounts",
  data() {
    return {
      institutions: [],
      groupName: "",
      groupStatus: ""
    };
  },
  methods: {
    async fetchInstitutions() {
      try {
        const res = await axios.get("/api/accounts/institutions");
        if (res.data.status === "success") {
          // Convert institutions object into an array for iteration and add an 'expanded' flag.
          this.institutions = Object.values(res.data.institutions).map(inst => ({
            ...inst,
            expanded: false
          }));
        }
      } catch (err) {
        console.error("Error fetching institutions:", err);
      }
    },
    toggleInstitution(inst) {
      inst.expanded = !inst.expanded;
    },
    linkNewAccount() {
      // Redirect or open a modal to link a new account (handled by your linking flow)
      this.$router.push({ name: "LinkAccount" });
    },
    async saveGroup() {
      try {
        const res = await axios.post("/api/accounts/save_group", {
          groupName: this.groupName,
          // For example, sending the list of institution IDs:
          accountIds: this.institutions.map(inst => inst.item_id)
        });
        this.groupStatus = res.data.message;
      } catch (err) {
        console.error("Error saving group:", err);
        this.groupStatus = "Failed to save group.";
      }
    }
  },
  mounted() {
    this.fetchInstitutions();
  }
};
</script>

<style scoped>
.institution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #1d1c22;
  padding: 10px;
  cursor: pointer;
  border-bottom: 1px solid #2f2730;
}
.institution-header h3 {
  margin: 0;
}
.last-refresh {
  font-size: 0.9em;
  color: gray;
}
.accounts-container {
  padding: 10px;
  background: rgb(74, 59, 75);
  border-left: 2px solid #4d3c3c;
  border-right: 2px solid #4d3c3c;
  border-bottom: 2px solid #4d3c3c;
}
.account-item {
  padding: 5px;
  border-bottom: 1px solid #4d3c3c;
}
.account-item:last-child {
  border-bottom: none;
}
.account-details {
  display: flex;
  justify-content: space-between;
}
.account-balance {
  font-weight: bold;
}
</style>
