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
import accountLinkApi from "@/api/accounts_link";
import { loadExternalScripts } from "@/utils/externalScripts";

export default {
  name: "LinkAccount",
  data() {
    return {
      scriptsLoaded: false,
      plaidLinkToken: null,
      tellerConnectInstance: null,
      userID: import.meta.env.VITE_USER_ID_PLAID || '',
      tellerAppId: import.meta.env.VITE_TELLER_APP_ID || '',
      tellerEnv: import.meta.env.VITE_TELLER_ENV || 'sandbox',
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
        const plaidRes = await accountLinkApi.generateLinkToken("plaid", {
          user_id: this.userID || "DefaultUser",
          products: ["transactions"],
        });
        this.plaidLinkToken = plaidRes.link_token;
      } catch (error) {
        console.error("Error generating Plaid link token:", error);
      }
    },
    async linkPlaid() {
      if (!this.scriptsLoaded || !this.plaidLinkToken || !window.Plaid) {
        console.error("Plaid linking prerequisites missing.");
        return;
      }

      const handler = window.Plaid.create({
        token: this.plaidLinkToken,
        onSuccess: async (public_token, metadata) => {
          try {
            const userID = this.userID || "DefaultUser";
            const exchangeRes = await accountLinkApi.exchangePublicToken("plaid", {
              public_token,
              user_id: userID,
            });
            console.log("Exchange response:", exchangeRes);

            await accountLinkApi.refreshCategories(); // Optional if you want to refresh categories after link

            this.$emit("refreshAccounts");
          } catch (error) {
            console.error("Error exchanging Plaid token:", error);
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
      if (!this.tellerAppId) {
        console.error("Missing Teller App ID.");
        return;
      }

      if (!this.tellerConnectInstance) {
        this.tellerConnectInstance = window.TellerConnect.setup({
          applicationId: this.tellerAppId,
          environment: this.tellerEnv,
          products: ["transactions", "balance"],
          onInit: () => {
            console.log("Teller Connect has initialized");
          },
          onSuccess: async (enrollment) => {
            console.log("User enrolled successfully", enrollment.accessToken);
            try {
              const exchangeRes = await accountLinkApi.exchangePublicToken("teller", {
                user_id: this.userID,
                public_token: enrollment.accessToken,
              });
              console.log("Teller exchange response:", exchangeRes);
            } catch (error) {
              console.error("Error exchanging Teller token:", error);
            }
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
  border: 1px solid var(--color-border-secondary);
  border-radius: 5px;
  padding: 1rem;
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
  background-color: var(--neon-mint);
}
</style>
