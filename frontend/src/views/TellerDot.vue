<template>
  <div class="teller-dot-page">
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
      <div class="connect-section">
        <!-- Teller Connect Button -->
        <button id="teller-connect">Connect to your bank</button>
      </div>
      <div class="accounts-table">
        <table id="linked-accounts">
          <thead>
            <tr>
              <th>Institution</th>
              <th>Account Name</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="3">No accounts linked yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: "TellerDot",
  mounted() {
    if (typeof TellerConnect === "undefined") {
      console.error("TellerConnect is not defined. Please include the Teller Connect script.");
      return;
    }

    // Load the application ID from environment variables
    const applicationId = import.meta.env.VITE_TELLER_APP_ID;
    if (!applicationId) {
      console.error("Application ID not found. Please set VITE_TELLER_APP_ID in your .env file.");
      return;
    }

    // Set up Teller Connect
    const tellerConnect = TellerConnect.setup({
      applicationId,
      products: ["transactions", "balance"],
      onInit: function () {
        console.log("Teller Connect has initialized");
      },
      onSuccess: async function (enrollment) {
        console.log("User enrolled successfully", enrollment);

        // Send the token to your backend for secure storage
        try {
          const response = await fetch("/api/teller/save_token", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              access_token: enrollment.accessToken,
              user_id: enrollment.user.id,
              enrollment_id: enrollment.enrollment.id,
              institution: enrollment.enrollment.institution.name,
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to save token");
          }

          const data = await response.json();
          if (data.status === "success") {
            console.log("Token saved successfully");
          } else {
            console.error("Error saving token:", data.message);
          }
        } catch (error) {
          console.error("Error saving token:", error);
        }
      },
      onExit: function () {
        console.log("User closed Teller Connect");
      },
    });

    // Attach Teller Connect to the button
    const connectButton = document.getElementById("teller-connect");
    if (connectButton) {
      connectButton.addEventListener("click", () => {
        tellerConnect.open();
      });
    }
  },
};
</script>

<style scoped>
.teller-dot-page {
  font-family: Arial, sans-serif;
}

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

.connect-section {
  margin: 20px 0;
  text-align: center;
}

#teller-connect {
  background-color: #3498db;
  color: #fff;
  border: none;
  padding: 12px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.accounts-table {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

table th,
table td {
  padding: 8px;
  border: 1px solid #ddd;
  text-align: left;
}

table th {
  background: #f9f9f9;
}
</style>
