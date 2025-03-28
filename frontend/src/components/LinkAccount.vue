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
@import '@/styles/global-colors.css';

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
