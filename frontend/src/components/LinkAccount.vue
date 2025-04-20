<template>
  <div class="link-account">
    <h2>Link a New Account</h2>
    <div class="button-group">
      <button @click="linkPlaid">Plaid</button>
      <button @click="linkTeller">Teller.io</button>
      <button @click="$emit('manual-token-click')">Provide Access Token</button>
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
      userId: import.meta.env.VITE_USER_ID_PLAID,
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

              const saveRes = await api.saveTellerToken({
                user_id: this.userId,
                access_token: enrollment.accessToken,
              });

            console.log("Plaid exchange response:", exchangeRes);
          } catch (error) {
            console.error("Error exchanging Plaid Access token:", error);
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
  border-top: 8px inset var(--color-bg-secondary);
  border-bottom: 6px outset var(--color-text-muted);
  border-left: 8px inset var(--color-bg-secondary);
  border-right: 6px outset var(--color-text-muted);
  border-radius: 5px;
}
.link-account h2 {
  margin: 5px 1px;
  color: var(--neon-purple);
}
.button-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}
.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
}
.button-group button:hover {
  color: var(--themed-bg);
  border: 1px;
  background-color: var(--neon-mint);
}
</style>
