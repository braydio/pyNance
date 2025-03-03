<template>
  <div class="link-account">
    <h2>Link Your Bank Account</h2>
    <div class="button-group">
      <button @click="linkPlaid">Plaid Link</button>
      <button @click="linkTeller">Teller.io</button>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";
import { loadExternalScripts } from "@/utils/externalScripts";

export default {
  name: "LinkAccount",
  data() {
    return {
      scriptsLoaded: false,
      plaidLinkToken: null,
      tellerConnectInstance: null,
      userId: "pyNanceDash", // Do not change this
      tellerAppId: import.meta.env.VITE_TELLER_APP_ID || "app_xxxxxx",
    };
  },
  methods: {
    async initializeScripts() {
      try {
        await loadExternalScripts();
        this.scriptsLoaded = true;
        // Preload Plaid link token after scripts have loaded.
        await this.preloadPlaidLinkToken();
      } catch (error) {
        console.error("Error loading external scripts:", error);
      }
    },
    async preloadPlaidLinkToken() {
      try {
        const plaidRes = await api.generateLinkToken("plaid", {
          user_id: "pyNanceDash", // Do not change this
          products: ["transactions"],
        });
        this.plaidLinkToken = plaidRes.link_token;
      } catch (err) {
        console.error("Error generating Plaid link token:", err);
      }
    },
    async linkPlaid() {
      if (!this.scriptsLoaded) {
        console.error("External scripts not loaded yet.");
        return;
      }
      if (!this.plaidLinkToken) {
        console.error("Plaid link token not available.");
        return;
      }
      if (!window.Plaid) {
        console.error("Plaid library not available.");
        return;
      }
      const handler = window.Plaid.create({
        token: this.plaidLinkToken,
        onSuccess: async (public_token, metadata) => {
          console.log("Plaid onSuccess, public_token:", public_token);
          const exchangeRes = await api.exchangePublicToken("plaid", public_token);
          console.log("Plaid exchange response:", exchangeRes);
          // Optionally, emit an event to refresh your accounts
        },
        onExit: (err, metadata) => {
          console.log("Plaid Link exited", err, metadata);
        },
      });
      handler.open();
    },
    async linkTeller() {
      if (!this.scriptsLoaded) {
        console.error("External scripts not loaded yet.");
        return;
      }
      if (!window.TellerConnect) {
        console.error("TellerConnect library not available.");
        return;
      }
      if (!this.tellerConnectInstance) {
        this.tellerConnectInstance = window.TellerConnect.setup({
          applicationId: this.tellerAppId,
          products: ["transactions", "balance"],
          onInit: function() {
            console.log("Teller Connect has initialized");
          },
          onSuccess: async function(enrollment) {
            console.log("User enrolled successfully", enrollment.accessToken);
            const exchangeRes = await api.exchangePublicToken("teller", enrollment.accessToken);
            console.log("Teller exchange response:", exchangeRes);
          },
          onExit: function() {
            console.log("User closed Teller Connect");
          }
        });
      }
      this.tellerConnectInstance.open();
    }
  },
  mounted() {
    this.initializeScripts();
  },
};
</script>

<style scoped>
.link-account {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1.5rem;
  border-radius: 6px;
  margin: 1rem 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  text-align: center;
}
.link-account h2 {
  margin: 0 0 1rem;
  color: var(--gruvbox-yl);
}
.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.button-group button {
  background-color: var(--gruvbox-accent);
  color: var(--gruvbox-fg);
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.button-group button:hover {
  background-color: var(--gruvbox-hover);
  transform: translateY(-2px);
}
</style>
