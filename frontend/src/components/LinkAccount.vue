
<template>
  <div class="link-account-wrapper">
    <button class="btn btn-pill btn-outline" @click="showLinkOptions = !showLinkOptions">
      {{ showLinkOptions ? 'Hide' : 'Link Account' }}
    </button>

    <transition name="slide-vertical">
      <div v-if="showLinkOptions" class="link-account">
        <h2>Link a New Account</h2>
        <div class="button-group">
          <button @click="linkPlaid">Plaid</button>
          <button @click="linkTeller">Teller.io</button>
          <button @click="$emit('manual-token-click')">Provide Access Token</button>
        </div>
      </div>
    </transition>
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
      showLinkOptions: false,
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
        onSuccess: async (public_token) => {
          try {
            const exchangeRes = await accountLinkApi.exchangePublicToken("plaid", {
              public_token,
              user_id: this.userID || "DefaultUser",
            });
            console.log("Exchange response:", exchangeRes);
            await accountLinkApi.refreshCategories();
            this.$emit("refreshAccounts");
          } catch (error) {
            console.error("Error exchanging Plaid token:", error);
          }
        },
        onExit: (err) => {
          console.log("Plaid Link exited", err);
        },
      });
      handler.open();
    },
    async linkTeller() {
      if (!this.scriptsLoaded || !window.TellerConnect || !this.tellerAppId) {
        console.error("Missing Teller prerequisites.");
        return;
      }
      if (!this.tellerConnectInstance) {
        this.tellerConnectInstance = window.TellerConnect.setup({
          applicationId: this.tellerAppId,
          environment: this.tellerEnv,
          products: ["transactions", "balance"],
          onSuccess: async (enrollment) => {
            try {
              const exchangeRes = await accountLinkApi.exchangePublicToken("teller", {
                public_token: enrollment.accessToken,
                user_id: this.userID,
              });
              console.log("Teller exchange response:", exchangeRes);
            } catch (error) {
              console.error("Error exchanging Teller token:", error);
            }
          },
          onExit: () => console.log("User closed Teller Connect"),
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
.control-block {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-text-light);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px var(--shadow);
  width: 100%;
  max-width: 600px;
}

.control-block h2 {
  margin-bottom: 0.5rem;
  color: var(--neon-purple);
  text-align: center;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.button-group button:hover {
  background-color: var(--neon-mint);
  color: var(--themed-bg);
}
</style>


