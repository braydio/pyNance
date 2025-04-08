<template>
  <div class="link-account">
    <h2>Link a New Account</h2>
    <div class="button-group">
      <button @click="linkPlaid">Plaid</button>
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
      userId: import.meta.env.VITE_USER_ID_PLAID, // Fixed: added VITE_ prefix
      tellerAppId: import.meta.env.VITE_TELLER_APP_ID || "app_xxxxxx",
    };
  },
  methods: {
    async initializeScripts() {
      try {
        await loadExternalScripts();
        this.scriptsLoaded = true;
        await this.preloadPlaidLinkToken();
      } catch (error) {
        console.error("Error loading external scripts:", error);
      }
    },
    async preloadPlaidLinkToken() {
      try {
        const plaidRes = await api.generateLinkToken("plaid", {
          user_id: this.userId,
          products: ["transactions"],
        });
        this.plaidLinkToken = plaidRes.link_token;
      } catch (err) {
        console.error("Error generating Plaid link token:", err);
      }
    },
    async linkPlaid() {
      if (!this.scriptsLoaded || !this.plaidLinkToken || !window.Plaid) {
        console.error("Prerequisites missing for Plaid linking.");
        return;
      }

      const handler = window.Plaid.create({
        token: this.plaidLinkToken,
        onSuccess: async (public_token, metadata) => {
          try {
            console.log("Plaid onSuccess, public_token:", public_token);
            const exchangeRes = await api.exchangePublicToken("plaid", {
              user_id: this.userId,
              public_token: public_token,
            });
            console.log("Plaid exchange response:", exchangeRes);
          } catch (error) {
            console.error("Error exchanging Plaid public token:", error);
          }
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
          onInit: () => {
            console.log("Teller Connect has initialized");
          },
          onSuccess: async (enrollment) => {
            console.log("User enrolled successfully", enrollment.accessToken);
            const exchangeRes = await api.exchangePublicToken("teller", {
              user_id: this.userId,
              public_token: enrollment.accessToken,
            });
            console.log("Teller exchange response:", exchangeRes);
          },
          onExit: () => {
            console.log("User closed Teller Connect");
          },
        });
      }
      this.tellerConnectInstance.open();
    },
  },
  mounted() {
    this.initializeScripts();
  },
};
</script>

<style scoped>

.link-account {
  margin: 0 auto;
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-bg-secondary);
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--shadow);
}

.link-account h2 {
  margin: 5px 5px 1rem;
  color: var(--link-color);
}
.button-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}
.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: none;
  padding: 0.5rem 0.1rem;
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
